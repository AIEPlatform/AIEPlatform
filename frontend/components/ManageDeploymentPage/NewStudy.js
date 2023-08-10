import { React, useContext, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';

function NewStudy(props) {
    const [studyName, sStudyName] = useState("");
    let sTheStudies = props.sTheStudies;
    let sTheStudy = props.sTheStudy;
    let sCreatingNewStudy = props.sCreatingNewStudy;
    let deployment = props.deployment;
    const handleCreateStudy = () => {
        fetch('/apis/experimentDesign/study', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "name": studyName,
                "deployment": deployment
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] == 200) {
                    sTheStudies(data["studies"]);
                    sTheStudy(data['theStudy']);
                    sCreatingNewStudy(false);

                }
                else {
                    alert(data['message']);
                }
            })
    };

    return (
        <Box>
            <TextField label="Study name" value={studyName} onChange={(e) => sStudyName(e.target.value)}></TextField>
            <Box sx={{ mt: 2 }}><Button variant="contained" sx={{ mr: 3 }} onClick={handleCreateStudy}>Create</Button></Box>
        </Box>
    );
}


export default NewStudy;