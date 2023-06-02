import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';

function NewDeployment() {
    const [deploymentName, sDeploymentName] = useState("");
    const [deploymentDescription, sDeploymentDescription] = useState("");

    const handleCreateDeployment = () => {
        fetch('/apis/create_deployment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "name": deploymentName,
                "description": deploymentDescription, 
                "collaborators": ["chenpan"]
            })
        }).then(response => response.json())
            .then(data => {
                console.log(data);
                if(data['status_code'] === 200) {
                    alert("Deployment created successfully!");
                    sDeploymentName("");
                    sDeploymentDescription("");
                }
                else {
                    alert("Deployment creation failed!");
                }
            })
    }

    return (
        <Layout>
            <Head><title>New Deployment - DataArrow</title></Head>
            <Container>
                <TextField sx={{ mr: 3 }} label="Deployment name" value={deploymentName} onChange={(e) => sDeploymentName(e.target.value)}></TextField>
                <TextField sx={{ mr: 3 }} label="Deployment description" value={deploymentDescription} onChange={(e) => sDeploymentDescription(e.target.value)}></TextField>
                <Box sx = {{mt: 2}}><Button variant="contained" sx={{ mr: 3 }} onClick={handleCreateDeployment}>Create</Button></Box>
            </Container>

        </Layout>
    );
}


export default NewDeployment;