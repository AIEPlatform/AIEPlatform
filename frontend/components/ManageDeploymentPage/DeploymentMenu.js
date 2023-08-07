import { React, useState, useEffect } from 'react';
import { Typography, Box, Button, Container } from '@mui/material';
import { List, ListItem, ListItemText, Link } from '@mui/material';

function DeploymentMenu() {
    const [deployments, sDeployments] = useState([]);
    useEffect(() => {
        fetch('/apis/my_deployments')
            .then(response => response.json())
            .then(data => {
                sDeployments(data["my_deployments"]);
            });
    }, []);
    return (
        <Container>
            <Box>
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
    );
}


export default DeploymentMenu;