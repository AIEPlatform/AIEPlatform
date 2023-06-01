import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import VariableEditor from '../components/NewMOOCletPage/VariableEditor';
import MoocletNameEditor from '../components/NewMOOCletPage/MoocletNameEditor';
import VersionEditor from '../components/NewMOOCletPage/VersionEditor';
import PolicyEditor from '../components/NewMOOCletPage/PolicyEditor';
import ChoosePolicyGroup from '../components/NewMOOCletPage/ChoosePolicyGroup';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Layout from '../components/layout';
import Head from 'next/head';


function NewMOOClet() {
    // TODO: check there is any unsubmitted mooclet.
    let [moocletName, sMoocletName] = useState("");

    const [variables, sVariables] = useState([
    ])

    const [versions, sVersions] = useState([
    ])

    const [policies, sPolicies] = useState([
    ])

    const [choosePolicyGroup, sChoosePolicyGroup] = useState({}) // only useful when more than 2 policies.


    const createNewMooclet = async (e) => {
        e.preventDefault();


        const url = `/apis/create_and_init_mooclet`
        const request = new Request(url, {
            method: "post",
            body: JSON.stringify({
                moocletName: moocletName,
                variables: variables,
                versions: versions,
                policies: policies,
                choosePolicyGroup: choosePolicyGroup
            }),
            headers: {
                Accept: "application/json, text/plain, */*",
                "Content-Type": "application/json"
            }
        })
        fetch(request)
            .then(function (res) {
                return res.json()
            })
            .then(response => {
                if (response.status_code == 200) {
                    console.log("success");
                }

                else {
                    console.log(response.message);
                }
            })
            .catch(error => {
                console.log(error)
            })
    }

    return (
        <Layout>
            <Head><title>New MOOClet - DataArrow</title></Head>
            <Container>
                <Typography variant="p">Please following the steps to create your desgined MOOClet (adaptive experiments)</Typography>
                <Box>
                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Name</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <MoocletNameEditor moocletName={moocletName} sMoocletName={sMoocletName} />
                        </AccordionDetails>
                    </Accordion>

                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Variables</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <VariableEditor selectedVariables={variables} sSelectedVariables={sVariables} />
                        </AccordionDetails>
                    </Accordion>

                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Versions</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <VersionEditor inputFields={versions} sInputFields={sVersions} />
                        </AccordionDetails>
                    </Accordion>

                    {versions.length > 0 && <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Policy</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <PolicyEditor policies={policies} sPolicies={sPolicies} versions={versions} variables={variables}></PolicyEditor>
                        </AccordionDetails>
                    </Accordion>}


                    {policies.length >= 2 && <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Choose Policy Group</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <ChoosePolicyGroup choosePolicyGroup={choosePolicyGroup} sChoosePolicyGroup={sChoosePolicyGroup} policies={policies}>Choose Policy Group</ChoosePolicyGroup>
                        </AccordionDetails>
                    </Accordion>}
                </Box>
                <Button sx={{ width: '100%', mt: 2 }} variant='contained' onClick={(e) => {
                    createNewMooclet(e);
                }}>Create this MOOClet</Button>
            </Container>
        </Layout>
    );
}


export default NewMOOClet;