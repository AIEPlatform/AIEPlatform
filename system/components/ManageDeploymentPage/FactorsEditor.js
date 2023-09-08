import { React } from 'react';
import { Paper, TextField, Button, Box } from '@mui/material';

function VersionEditor(props) {
    let factors = props.factors;
    let sFactors = props.sFactors;

    const handleVersionNameChange = (index, event) => {
        let data = [...factors];
        data[index] = event.target.value;
        sFactors(data);
    }

    const addFields = () => {
        sFactors([...factors, `factor${factors.length + 1}`]);
    }

    const removeFields = (index) => {
        let data = [...factors];
        data.splice(index, 1)
        sFactors(data);
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