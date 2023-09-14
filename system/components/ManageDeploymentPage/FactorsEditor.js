import { React, useState } from 'react';
import { Paper, TextField, Button, Box, Typography } from '@mui/material';

function VersionEditor(props) {
    let [newFactor, sNewFactor] = useState("");
    let factors = props.factors;
    let sFactors = props.sFactors;

    const addFields = () => {
        try {
            // check if new factor exists aready.
            for (let i = 0; i < factors.length; i++) {
                if (factors[i] === newFactor) {
                    alert("Factor already exists.");
                    return;
                }
            }
            if (newFactor === "") sFactors([...factors, `factor${factors.length + 1}`]);
            else sFactors([...factors, newFactor]);
            sNewFactor("");
        }
        catch (e) {
            alert("Error when adding new factors. Please try again later.");
        }
    }

    const removeFields = (index) => {
        let data = [...factors];
        data.splice(index, 1)
        sFactors(data);
    }

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>

            <Box>
                <TextField sx={{ mb: 2, mr: 2 }} label="New factor name" variant="standard" value={newFactor} InputLabelProps={{ shrink: true }} onChange={(e) => sNewFactor(e.target.value)} />
                <Button onClick={(e) => addFields()} variant="contained" color="primary" sx={{ marginTop: "10px" }}>Add a factor</Button>
            </Box>
            <Typography variant="h5">Current Factors</Typography>
            {factors.map((factor, index) => {
                return (
                    <Box key={factor} margin="10px 0" style={{ position: "relative" }}>
                        <TextField sx={{ mb: 2, mr: 2 }} label="Factor" variant="standard" value={factor} InputLabelProps={{ shrink: true }} disabled={true} />
                        <Button onClick={() => removeFields(index)} variant="contained" style={{ marginTop: "10px" }} color="error">Remove</Button>
                    </Box>
                )
            })}
        </Paper>
    )
}


export default VersionEditor;