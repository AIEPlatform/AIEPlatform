import { React, useContext, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';

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
                "collaborators": []
            })
        }).then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    window.open(`/deployments/${deploymentName}`,"_self");
                }
                else {
                    alert(data['message']);
                }
            })
    }

    return (
        <Container>
            <TextField sx={{ mr: 3 }} label="Deployment name" value={deploymentName} onChange={(e) => sDeploymentName(e.target.value)}></TextField>
            <TextField sx={{ mr: 3, mt: 3 }} label="Deployment description" value={deploymentDescription} onChange={(e) => sDeploymentDescription(e.target.value)} maxRows={10} multiline fullWidth></TextField>
            <Box sx={{ mt: 2 }}><Button variant="contained" sx={{ mr: 3 }} onClick={handleCreateDeployment}>Create</Button></Box>
        </Container>
    );
}


export default NewDeployment;