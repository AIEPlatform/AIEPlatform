import { React, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';

import { Typography, Box, Button, Container, Link } from '@mui/material';
import Layout from '../../components/layout';
import Head from 'next/head';
import Select from 'react-select';
import StudyEditor from '../../components/ManageDeploymentPage/StudyEditor';
import { UserContext } from "../../contexts/UserContextWrapper";
import DeleteIcon from '@mui/icons-material/Delete';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import LockOpenIcon from '@mui/icons-material/LockOpen';

import getConfig from 'next/config';
import { usePathname } from 'next/navigation'

const { publicRuntimeConfig } = getConfig();
const websiteName = publicRuntimeConfig.websiteName;


const newStudy = {
    "name": "Create New Study",
    "_id": { "$oid": "1998" }
}

function ManageDeployment() {
    const router = useRouter();
    const { deployment } = router.query;
    const [theStudies, sTheStudies] = useState([]);
    const [theStudy, sTheStudy] = useState(null);
    const [theDeployment, sTheDeployment] = useState(null);
    const { userContext, sUserContext } = useContext(UserContext);

    const [permissionError, sPermissionError] = useState(false);
    const [permissionErrorRedirectionCounter, sPermissionErrorRedirectionCounter] = useState(5);
    useEffect(() => {
        if (userContext !== undefined && userContext === null) {
            window.location.href = "/Login";
        }
    }, [userContext]);

    useEffect(() => {
        if (deployment === undefined) return;
        fetch(`/apis/experimentDesign/deployment?deployment_name=${deployment}`)
            .then(response => response.json())
            .then(data => {
                if (data["status_code"] === 200) {
                    sTheDeployment(data["deployment"]);
                }
                else {
                    sPermissionError(true);
                    setTimeout(function() {
                        window.location.href = "/deployments"; // Replace with the URL you want to redirect to
                    }, 5000);

                    // update permissionErrorRedirectionCounter every second.

                    setInterval(
                        function() {
                            sPermissionErrorRedirectionCounter((permissionErrorRedirectionCounter) => permissionErrorRedirectionCounter - 1);
                        }, 1000
                    )
                }
            });
    }, [deployment]);


    useEffect(() => {
        if (theDeployment === null) return;
        fetch(`/apis/experimentDesign/the_studies/?deployment_name=${theDeployment['name']}`)
            .then(response => response.json())
            .then(data => {
                sTheStudies([newStudy].concat(data["studies"]));
            });
    }, [theDeployment]);

    const handleSelectStudy = (option) => {
        sTheStudy(option);
    }

    const handleDeleteDeployment = () => {
        if (!confirm("Are you sure you want to delete the deployment? All studies will be deleted. The interactions/datasets associated will all be deleted.")) return;
        fetch(`/apis/experimentDesign/deployment`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                deployment: theDeployment['name']
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    // refresh
                    window.location.replace("/deployments");
                }
                else {
                    alert("Failed to delete deployment");
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                alert("Failed to delete deployment");
            });
    };


    const handleDeploymentTokenUpdate = () => {
        // put api to /apis/experimentDesign/generateDeploymentApiToken with deployment in the request body
        if (!confirm("Are you sure you want to generate/update the api token? If you have used the apis, you may need to add the api token in the header.")) return;
        fetch(`/apis/experimentDesign/generateDeploymentApiToken`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                deployment: theDeployment['name']
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    // refresh
                    sTheDeployment(data['theDeployment']);
                }
                else {
                    alert("Failed to generate deployment token");
                }
            }
            )
            .catch((error) => {
                console.error('Error:', error);
                alert("Failed to generate deployment token");
            }
            );
    }


    const handleDeploymentTokenDelete = () => {
        // put api to /apis/experimentDesign/generateDeploymentApiToken with deployment in the request body

        fetch(`/apis/experimentDesign/deleteDeploymentApiToken`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                deployment: theDeployment['name']
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    // refresh
                    sTheDeployment(data['theDeployment']);
                }
                else {
                    alert("Failed to delete deployment token");
                }
            }
            )
            .catch((error) => {
                console.error('Error:', error);
                alert("Failed to delete deployment token");
            }
            );
    }

    if (userContext !== undefined && userContext !== null && !permissionError) {
        return (
            <Layout>
                <Head><title>Manage Deployment - {websiteName}</title></Head>
                <Container>
                    <Box>
                        <Link href="/deployments">Back to see my deployments</Link>
                        <Typography variant="h5">{deployment}</Typography>
                        {theDeployment &&
                            <Box>
                                <Box>
                                    <Button sx={{ m: 1, ml: 0 }} variant="outlined" startIcon={<DeleteIcon />} onClick={handleDeleteDeployment}>Delete</Button>
                                    <Button sx={{ m: 1 }} variant="outlined" startIcon={<RestartAltIcon />} onClick={() => alert("Not complete yet! But you can reset each study.")}>Reset</Button>
                                </Box>
                                <Box>
                                    {!theDeployment['apiToken'] && <Button sx={{ m: 1, ml: 0 }} variant="outlined" startIcon={<VpnKeyIcon />} onClick={handleDeploymentTokenUpdate}>Generate Token</Button>}
                                    {theDeployment['apiToken'] && <Button sx={{ m: 1, ml: 0 }} variant="outlined" startIcon={<VpnKeyIcon />} onClick={handleDeploymentTokenUpdate}>Re-generate Token</Button>}
                                    {theDeployment['apiToken'] && <Button sx={{ m: 1 }} variant="outlined" startIcon={<LockOpenIcon />} onClick={handleDeploymentTokenDelete}>Delete Token</Button>}
                                </Box>
                                {theDeployment['apiToken'] && <Typography variant="body1">Token: {theDeployment['apiToken']}</Typography>}
                            </Box>
                        }
                    </Box>


                    <Box>
                        <Typography variant="h6">Study</Typography>
                        <Select
                            options={theStudies}
                            getOptionLabel={(option) => option["name"]}
                            getOptionValue={(option) => option["_id"]["$oid"]}
                            value={theStudy}
                            onChange={(option) => handleSelectStudy(option)}
                            placeholder="Select a study"
                        />
                    </Box>
                </Container>
                {theStudy && <StudyEditor deploymentName={theDeployment['name']} theStudy={theStudy} sTheStudies={sTheStudies} sTheStudy={sTheStudy}></StudyEditor>}
            </Layout>
        );
    }

    if (userContext !== undefined && userContext !== null && permissionError) {
        return (
            <Layout>
                <Head><title>Manage Deployment - {websiteName}</title></Head>
                <Container>
                    You don't have access to this deployment. You will be redirected in {permissionErrorRedirectionCounter} seconds...
                </Container>
            </Layout>
        );
    }
}


export default ManageDeployment;