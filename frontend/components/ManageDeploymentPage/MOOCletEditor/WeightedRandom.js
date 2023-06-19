import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function WeightedRandom(props) {
    let versions = props.versions;
    let mooclets = props.mooclets;
    let myId = props.myId;
    let sMooclets = props.sMooclets;
    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);

    let handleWeightChange =(index, event) => {
        let data = [...mooclets];
        let mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['parameters'][versions[index]['name']] = Number(event.target.value);
        sMooclets(data);
    }
    return (
        <Box>
            Edit weights for the versions.
            You don't have to make sure they sum to 1. But please note that the higher the weight, the more likely the version will be sampled.
            {
                versions.map((version, index) => {
                    return (
                        <Box key = {index} sx={{mt: 2}}>
                            <TextField
                                required
                                value={mooclet['parameters'][versions[index]['name']] ? mooclet['parameters'][versions[index]['name']] : ""}
                                label={`Version(${index+1}) weight`}
                                onChange={(e) => handleWeightChange(index, e)}
                                type="number"
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