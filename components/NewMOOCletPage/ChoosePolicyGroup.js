import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function choosePolicyGroup(props) {
    let choosePolicyGroup = props.choosePolicyGroup;
    let policies = props.policies;
    let sChoosePolicyGroup = props.sChoosePolicyGroup;

    let handleWeightChange =(index, event) => {
        // let data = [...choosePolicyGroup];
        // // data[index]['weight'] = event.target.value;
        // // sChoosePolicyGroup(data);
        // console.log(data)
    }
    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Typography variant="h6">Edit weights for the policies.</Typography>
            {
                policies.map((policy, index) => {
                    return (
                        <Box key = {index}>
                            <Typography>{`Policy(${index+1}) - ${policy.type}: `}</Typography>
                            <TextField
                                required
                                label={`Weight`}
                                onChange={(e) => handleWeightChange(index, e)}
                                type="number"
                                InputProps={{ inputProps: { min: 0, max: 1 } }}
                                fullWidth
                            />
                        </Box>
                    )
                })
            }
        </Paper>
    )
}


export default choosePolicyGroup;