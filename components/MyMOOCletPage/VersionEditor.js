import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';


// This is the version editor for the existing mooclet! Different from the Version Editor for the new MOOClet.
function VersionEditor(props) {
    let versions = props.versions;
    let sVersions = props.sVersions;

    const handleFormChange = (index, event) => {
        let data = [...versions];
        data[index]['text'] = event.target.value;
        sVersions(data);

        console.log(versions)
    }

    const addFields = () => {
        let newfield = {}
        sVersions([...versions, newfield])
    }

    const removeFields = (index) => {
        let data = [...versions];
        data.splice(index, 1)
        sVersions(data)
    }

    return (
        <Paper sx={{
            m:1, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {versions.map((input, index) => {
                return (
                    <Box key={index} margin = "10px 0" style={{position: "relative"}}>
                        <Typography>{`Version(${index + 1}) content`}</Typography>
                        <TextField
                            required
                            onChange={(e) => handleFormChange(index, e)}
                            rows="2"
                            value={input['text']}
                            multiline
                            fullWidth
                        />
                        <Button onClick={() => removeFields(index)} variant="contained" style={{marginTop: "10px"}} color="error">Remove</Button>
                    </Box>
                )
            })}

        <Button onClick = {(e) => addFields()} variant="contained" color="primary" sx = {{m: 1}}>Add More Versions</Button>
        </Paper>
    )
}


export default VersionEditor;