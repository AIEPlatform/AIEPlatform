import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem } from '@mui/material';

function TSConfigurable(props) {
    let versions = props.versions;
    let policyIndex = props.policyIndex;
    let policies = props.policies;
    let sPolicies = props.sPolicies;
    let variables = props.variables;

    let handleWeightChange = (event, name) => {
        let data = [...policies];
        data[policyIndex]['parameter'][name] = event.target.value;
        sPolicies(data);
        console.log(data)
    }
    
    return (
        <Box>
            <TextField
                required
                label={`Prior Success`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'prior-success')}
            />
            <TextField
                required
                label={`Prior Failure`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'prior-failure')}
            />
            <TextField
                required
                label={`Max Rating`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'max_rating')}
            />
            <TextField
                required
                label={`Min Rating`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'min_rating')}
            />
            <TextField
                required
                label={`Uniform Threshold`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'uniform_threshold')}
            />
            <TextField
                required
                label={`TSPostDiff Threshold`}
                type="number"
                onChange = {(e) => handleWeightChange(e, 'tspostdiff_thresh')}
            />
            <Box>
                <TextField
                    id="select-reward"
                    select
                    width="100px"
                    label="Select a reward"
                    onChange = {(e) => handleWeightChange(e, 'outcome_variable_name')}
                >
                    {variables.map(( variable, index) => (
                        <MenuItem key={index} value={variable.name}>
                            {variable.name}
                        </MenuItem>
                    ))}
                </TextField>
            </Box>
        </Box >
    )
}


export default TSConfigurable;