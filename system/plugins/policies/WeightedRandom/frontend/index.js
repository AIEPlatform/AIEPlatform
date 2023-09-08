import React, { useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';
import CommonAssignerAttribute from '../../CommonAssignerAttributes';


export function validate(props) {
    let assigner = props.assigner;
    let parameters = assigner['parameters'];
    let factors = props.factors;
    let variables = props.variables;
    let versions = props.versions;
    let existingVariables = props.existingVariables;

    for (const key in assigner['parameters']) {
        if (!versions.some(obj => obj['name'] === key)) {
          delete assigner['parameters'][key];
        }
      }
}

export const name = "Weighted Random";

export function main(props) {
    let versions = props.versions;
    let assigners = props.assigners;
    let myId = props.myId;
    let sAssigners = props.sAssigners;
    let tree = [...assigners];
    let assigner = tree.find(assigner => assigner.id === myId);

    let handleWeightChange =(index, event) => {
        let data = [...assigners];
        let assigner = data.find(assigner => assigner.id === myId);
        assigner['parameters'][versions[index]['name']] = event.target.value;
        sAssigners(data);
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
                                value={assigner['parameters'][versions[index]['name']] ? assigner['parameters'][versions[index]['name']] : ""}
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