import { React, useContext, useState, useEffect } from 'react';
import { Typography, Box, Button, Container } from '@mui/material';
import Layout from '../../components/layout';
import Head from 'next/head';
import { UserContext } from "../../contexts/UserContextWrapper";
import { List, ListItem, ListItemText, Link, Tabs, Tab } from '@mui/material';
import NewDeployment from '../../components/ManageDeploymentPage/NewDeployment';
import DeploymentMenu from '../../components/ManageDeploymentPage/DeploymentMenu';

import getConfig from 'next/config';

const { publicRuntimeConfig } = getConfig();
const websiteName = publicRuntimeConfig.websiteName;

function ManageDeployment() {
    const [deployments, sDeployments] = useState([]);
    const { userContext, sUserContext } = useContext(UserContext);
    const [tabIndex, sTabIndex] = useState(0);
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

                <Container sx={{mb: 2}}>
                    <Tabs value={tabIndex} onChange={(e, newValue) => {sTabIndex(newValue)}} aria-label="basic tabs example">
                        <Tab label="Deployment Menu"/>
                        <Tab label="Create New Deployment"/>
                    </Tabs>
                </Container>
                {tabIndex === 0 && <DeploymentMenu />}

                {tabIndex === 1 && <NewDeployment />}
            </Layout>
        );
    }
}


export default ManageDeployment;