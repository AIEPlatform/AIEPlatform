import { React, useContext, useState, useEffect } from 'react';
import { Typography, Box, Button, Container } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import { UserContext } from "../contexts/UserContextWrapper";
import { List, ListItem, ListItemText, Link } from '@mui/material';
import NewDeployment from '../components/ManageDeploymentPage/NewDeployment';

import getConfig from 'next/config';

const { publicRuntimeConfig } = getConfig();
const websiteName = publicRuntimeConfig.websiteName;

function ManageDeployment() {
    const [deployments, sDeployments] = useState([]);
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
                sDeployments(data["my_deployments"]);
            });
    }, []);

    if (userContext !== undefined && userContext !== null) {
        return (
            <Layout>
                <Head><title>Manage Deployment - {websiteName}</title></Head>
                <Container>
                    <Box>
                        <Typography variant="h6">Find a deployment, or make a new one!</Typography>
                        {/* Make a list with href. */}

                        <List>
                            {deployments.map((deployment) => (
                                <Box key={deployment.name}>
                                    <Link href={`/deployments/${deployment.name}`} variant='h6'>{deployment.name}</Link>
                                    <Box><small>{deployment.description}</small></Box>
                                </Box>
                            ))}
                        </List>
                    </Box>
                </Container>
                
                <NewDeployment />
            </Layout>
        );
    }
}


export default ManageDeployment;