import { React, useState } from 'react';
import { Typography, Paper, TextField, Button, Box } from '@mui/material';

function VersionEditor(props) {
    let versions = props.versions;
    let sVersions = props.sVersions;
    let factors = props.factors;

    const handleFormChange = (index, event) => {
        let data = [...versions];
        data[index]['content'] = event.target.value;
        sVersions(data);
    }

    const handleVersionNameChange = (index, event) => {
        let data = [...versions];
        data[index]['name'] = event.target.value;
        sVersions(data);
    }

    const addFields = () => {
        let versionJSON = {};
        factors.forEach((factor) => {
            versionJSON[factor] = 0;
        })
        let newfield = { name: `version${versions.length + 1}`, content: '', versionJSON: versionJSON }
        sVersions([...versions, newfield]);
        // Need to set all factors to 0 for this new version.
    }

    const removeFields = (index) => {
        let data = [...versions];
        data.splice(index, 1)
        sVersions(data);
    }

    const handleVersionJSONChange = (index, factor, e) => {
        let data = [...versions];
        data[index]['versionJSON'][factor] = isNaN(e.target.value) ? 0 : parseFloat(e.target.value);
        sVersions(data);
    }

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {versions.map((input, index) => {
                return (
                    <Box key={index} margin="10px 0" style={{ position: "relative" }}>
                        <TextField sx={{ mb: 2 }} label="Version Name" variant="standard" value={input['name']} InputLabelProps={{ shrink: true }} onChange={(e) => handleVersionNameChange(index, e)} />
                        <TextField
                            required
                            label={`${input['name']}`}
                            onChange={(e) => { handleFormChange(index, e) }}
                            value={input['content']}
                            rows="2"
                            multiline
                            fullWidth
                        />

                        <Box sx = {{mt: 2, mr: 2}}>
                            <p>Version JSON</p>
                            {factors.map((factor, _) => (
                                <TextField
                                    sx={{mr: 2, mb: 2}}
                                    key={factor}
                                    label={factor}
                                    value={input['versionJSON'][factor]}
                                    type="number"
                                    onChange={(e) => { handleVersionJSONChange(index, factor, e)}}
                                />
                            ))}
                        </Box>
                        <Button onClick={() => removeFields(index)} variant="contained" style={{ marginTop: "10px" }} color="error">Remove</Button>
                    </Box>
                )
            })}

            <Button onClick={(e) => addFields()} variant="contained" color="primary" sx={{ m: 1 }}>Add More Versions</Button>
        </Paper>
    )
}


export default VersionEditor;