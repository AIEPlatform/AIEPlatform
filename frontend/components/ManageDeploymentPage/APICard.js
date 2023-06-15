import * as React from 'react';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';

export default function APICard(props) {
    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <mark>Complete API doc is not available yet, sorry!</mark>
            <Box key="get_treatment" margin = "10px 0" style={{position: "relative"}}>
                        <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            To get an arm for a user for a specific study and deployment.
                        </Typography>
                        <Typography variant="h5" component="div">
                            /get_treatment
                        </Typography>
                        <Typography sx={{ mb: 1.5 }} color="text.secondary">
                            POST
                        </Typography>
                        <Typography variant="body2">
                            <mark>Request Body</mark>
                            <pre>{JSON.stringify({
                                "deployment": props.deploymentName,
                                "study": props.studyName,
                                "user": "chenpan",
                                "where": "OPTIONAL"
                            }, null, 2)}</pre>
                            <mark>Sample Response</mark>
                            <pre>{JSON.stringify({ "treatment": { "name": "version2", "content": "2" } }, null, 2)}</pre>
                            <mark>treatment is an object that represents the name and content of the assigned treatment</mark>
                        </Typography>
            </Box>

            <Box key="give_reward" margin = "10px 0" style={{position: "relative"}}>
                        <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            To send a reward by a user for a specific study and deployment.
                        </Typography>
                        <Typography variant="h5" component="div">
                            /give_reward
                        </Typography>
                        <Typography sx={{ mb: 1.5 }} color="text.secondary">
                            POST
                        </Typography>
                        <Typography variant="body2">
                            <mark>Request Body</mark>
                            <pre>{JSON.stringify({
                                "deployment": props.deploymentName,
                                "study": props.studyName,
                                "user": "chenpan",
                                "where": "OPTIONAL",
                                "value": "reward value"
                            }, null, 2)}</pre>
                            <mark>Sample Response</mark>
                            <pre>{JSON.stringify({ "status_code": 200 }, null, 2)}</pre>
                        </Typography>
            </Box>

            <Box key="give_variable" margin = "10px 0" style={{position: "relative"}}>
                        <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
                            To send a value for a variable by a user.
                        </Typography>
                        <Typography variant="h5" component="div">
                            /give_variable
                        </Typography>
                        <Typography sx={{ mb: 1.5 }} color="text.secondary">
                            POST
                        </Typography>
                        <Typography variant="body2">
                            <mark>Request Body</mark>
                            <pre>{JSON.stringify({
                                "deployment": props.deploymentName,
                                "study": props.studyName,
                                "user": "chenpan",
                                "variableName": "wantToTravel",
                                "value": "variable value"
                            }, null, 2)}</pre>
                            <mark>Sample Response</mark>
                            <pre>{JSON.stringify({ "status_code": 200 }, null, 2)}</pre>
                        </Typography>
            </Box>
        </Paper>

    );
}
