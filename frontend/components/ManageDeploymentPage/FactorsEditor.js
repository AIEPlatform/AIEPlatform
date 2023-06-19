import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function VersionEditor(props) {
    let factors = props.factors;
    let sFactors = props.sFactors;
    let versions = props.versions;
    let sVersions = props.sVersions;

    const handleVersionNameChange = (index, event) => {
        let data = [...factors];
        data[index] = event.target.value;
        sFactors(data);
    }

    const addFields = () => {
        sFactors([...factors, `factor${factors.length + 1}`]);
        // Need to add this factor to every versionJSON in versions.
        let data = [...versions];
        data.forEach((version) => {
            version['versionJSON'][`factor${factors.length + 1}`] = 0;
        }
        )
        sVersions(data);
    }

    const removeFields = (index) => {
        let data = [...factors];
        data.splice(index, 1)
        sFactors(data);

        // Need to remove this factor to every versionJSON in versions.
        let data2 = [...versions];
        data2.forEach((version) => {
            delete version['versionJSON'][factors[index]]
        }
        )
        sVersions(data2);
    }

    return (
        <Paper sx={{
            m:1, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {factors.map((factor, index) => {
                return (
                    <Box key={factor} margin = "10px 0" style={{position: "relative"}}>
                        <TextField sx = {{mb: 2, mr: 2}} label="Factor" variant="standard" value = {factor} InputLabelProps={{ shrink: true }} onChange={(e) => handleVersionNameChange(index, e)}/>
                        <Button onClick={() => removeFields(index)} variant="contained" style={{marginTop: "10px"}} color="error">Remove this factor</Button>
                    </Box>
                )
            })}

        <Button onClick = {(e) => addFields()} variant="contained" color="primary" sx = {{m: 1}}>Add a factor</Button>

        <mark>Renaming an existing factor is equivalent to removing this factor and creating another!</mark>
        </Paper>
    )
}


export default VersionEditor;