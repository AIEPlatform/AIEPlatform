import { React, useContext, useState, useEffect } from 'react';
import { Typography, Box, Button, Container } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import Select from 'react-select';
import StudyEditor from '../components/ManageDeploymentPage/StudyEditor';
import { UserContext } from "../contexts/UserContextWrapper";
import DeleteIcon from '@mui/icons-material/Delete';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import LockOpenIcon from '@mui/icons-material/LockOpen';

import getConfig from 'next/config';

const { publicRuntimeConfig } = getConfig();
const websiteName = publicRuntimeConfig.websiteName;


const newStudy = {
    "name": "Create New Study",
    "_id": { "$oid": "1998" }
}

function ManageDeployment() {
    const [myDeployments, sMyDeployments] = useState([]);
    const [theStudies, sTheStudies] = useState([]);
    const [theStudy, sTheStudy] = useState(null);
    const [theDeployment, sTheDeployment] = useState(null);

    const { userContext, sUserContext } = useContext(UserContext);
    useEffect(() => {
        if (userContext !== undefined && userContext === null) {
            window.location.href = "/Login";
        }
    }, [userContext]);

    useEffect(() => {
        fetch('/apis/my_deployments')
            .then(response => response.json())
            .then(data => {
                sMyDeployments(data["my_deployments"]);
            });
    }, []);

    const handleSelectMyDeployment = (option) => {
        fetch(`/apis/experimentDesign/the_studies/?deployment_id=${option["_id"]["$oid"]}`)
            .then(response => response.json())
            .then(data => {
                sTheStudies([newStudy].concat(data["studies"]));
                sTheDeployment(option)
            });
    }

    const handleSelectStudy = (option) => {
        sTheStudy(option);
    }

    const handleDeleteDeployment = () => {
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
                    location.reload();
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
                    sMyDeployments(data['deployments']);
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
                    sMyDeployments(data['deployments']);
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

    if (userContext !== undefined && userContext !== null) {
        return (
            <Layout>
                <Head><title>Manage Deployment - {websiteName}</title></Head>
                <Container>
                    <Box>
                        <Typography variant="h6">Deployment</Typography>
                        <Select
                            options={myDeployments}
                            getOptionLabel={(option) => option["name"]}
                            getOptionValue={(option) => option["_id"]["$oid"]}
                            onChange={(option) => handleSelectMyDeployment(option)}
                            placeholder="Select a deployment"
                        />
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
}


export default ManageDeployment;