import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function VersionEditor(props) {
    let inputFields = props.inputFields;
    let sInputFields = props.sInputFields;

    const handleFormChange = (index, event) => {
        let data = [...inputFields];
        data[index]['content'] = event.target.value;
        sInputFields(data);
    }

    const handleVersionNameChange = (index, event) => {
        let data = [...inputFields];
        data[index]['name'] = event.target.value;
        sInputFields(data);
    }

    const addFields = () => {
        let newfield = {name: `version${inputFields.length + 1}`, content: ''}
        sInputFields([...inputFields, newfield])
    }

    const removeFields = (index) => {
        let data = [...inputFields];
        data.splice(index, 1)
        sInputFields(data)
    }

    return (
        <Paper sx={{
            m:1, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {inputFields.map((input, index) => {
                return (
                    <Box key={index} margin = "10px 0" style={{position: "relative"}}>
                        <TextField sx = {{mb: 2}} label="Version Name" variant="standard" value = {input['name']} InputLabelProps={{ shrink: true }} onChange={(e) => handleVersionNameChange(index, e)}/>
                        <TextField
                            required
                            label={`${input['name']}`}
                            onChange={(e) => {handleFormChange(index, e)}}
                            value={input['content']}
                            rows="2"
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