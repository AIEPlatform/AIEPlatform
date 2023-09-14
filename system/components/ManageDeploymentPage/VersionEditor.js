import { React, useState } from 'react';
import { Paper, TextField, Button, Box, Typography } from '@mui/material';

function VersionEditor(props) {
    let versions = props.versions;
    let sVersions = props.sVersions;
    let factors = props.factors;

    let [newVersionName, sNewVersionName] = useState("");

    const handleFormChange = (index, event) => {
        let data = [...versions];
        data[index]['content'] = event.target.value;
        sVersions(data);
    }

    const addFields = () => {
        // check if version name already exists.
        try {
            for (let i = 0; i < versions.length; i++) {
                if (versions[i]['name'] === newVersionName) {
                    alert("Version name already exists.");
                    return;
                }
            }
            let versionJSON = {};
            factors.forEach((factor) => {
                versionJSON[factor] = 0;
            })

            let name = `version${versions.length + 1}`;
            if (newVersionName !== "") {
                name = newVersionName;
            }
            let newfield = { name: name, content: '', versionJSON: versionJSON }
            sVersions([...versions, newfield]);
            sNewVersionName("");
            // Need to set all factors to 0 for this new version.
        }
        catch (e) {
            alert("Error when adding new version. Please try again later.");
        }
    }

    const removeFields = (index) => {
        let data = [...versions];
        data.splice(index, 1)
        sVersions(data);
    }

    const handleVersionJSONChange = (index, factor, e) => {
        let data = [...versions];
        data[index]['versionJSON'][factor] = e.target.value;
        sVersions(data);
    }

    // state: tinymce version index.
    let setTinyMCEEditorIndex = props.setTinyMCEEditorIndex;

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>

            <Box>
                <TextField sx={{ mb: 2, mr: 2 }} label="New version name" variant="standard" value={newVersionName} InputLabelProps={{ shrink: true }} onChange={(e) => sNewVersionName(e.target.value)} />
                <Button onClick={(e) => addFields()} variant="contained" color="primary" sx={{ marginTop: "10px" }}>Add a new version</Button>
            </Box>
            <Typography variant="h5">Current Versions</Typography>
            {versions.map((input, index) => {
                return (
                    // add a seperator line.
                    <Box key={index} margin="10px 0" style={{ position: "relative" }}>
                        <Typography variant="h6" sx={{ m: 1 }}>{input['name']}</Typography>

                        <Box sx={{ display: 'flex', flexDirection: 'row', mb: 2 }}>
                            <Button onClick={() => removeFields(index)} variant="contained" style={{ marginTop: "10px" }} color="error">Remove</Button>
                            <Button onClick={() => setTinyMCEEditorIndex(index)} variant="contained" style={{ marginTop: "10px", marginLeft: "10px" }} color="primary">Edit</Button>
                        </Box>
                        <TextField
                            required
                            label={`${input['name']}`}
                            onChange={(e) => { handleFormChange(index, e) }}
                            value={input['content']}
                            rows="2"
                            multiline
                            fullWidth
                        />

                        <Box sx={{ mt: 2, mr: 2 }}>
                            <p>Version JSON</p>
                            {factors.map((factor, _) => (
                                <TextField
                                    sx={{ mr: 2, mb: 2 }}
                                    key={factor}
                                    label={factor}
                                    value={input['versionJSON'][factor] ? input['versionJSON'][factor] : ""}
                                    type="number"
                                    onChange={(e) => { handleVersionJSONChange(index, factor, e) }}
                                />
                            ))}
                        </Box>
                    </Box>
                )
            })}
        </Paper>
    )
}


export default VersionEditor;