import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function WeightedRandom(props) {
    let versions = props.versions;
    let policyIndex = props.policyIndex;
    let policies = props.policies;
    let sPolicies = props.sPolicies;

    let handleWeightChange =(index, event) => {
        console.log(policies[policyIndex])
        let data = [...policies];
        data[policyIndex]['parameter'][`version-${index+1}`] = Number(event.target.value);
        sPolicies(data);
    }
    return (
        <Box>
            Edit weights for the versions.
            {
                versions.map((version, index) => {
                    return (
                        <Box key = {index}>
                            <TextField
                                required
                                label={`Version(${index+1}) weight`}
                                onChange={(e) => handleWeightChange(index, e)}
                                type="number"
                                InputProps={{ inputProps: { min: 0, max: 1 } }}
                                fullWidth
                            />
                            <Box><Typography style={{overflowWrap: "break-word"}}>Version Content: {version.content}</Typography></Box>
                        </Box>
                    )
                })
            }
        </Box>
    )
}


export default WeightedRandom;