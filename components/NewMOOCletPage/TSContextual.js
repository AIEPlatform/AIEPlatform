import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem } from '@mui/material';
import Select from 'react-select';
const options = [
    { value: 'ocean', label: 'Ocean' },
    { value: 'blue', label: 'Blue' }
]
function TSConfigurable(props) {
    let versions = props.versions;
    let policyIndex = props.policyIndex;
    let policies = props.policies;
    let sPolicies = props.sPolicies;
    let variables = props.variables;

    let handleWeightChange = (event, name) => {
        let data = [...policies];
        data[policyIndex]['parameter'][name] = Number(event.target.value);
        sPolicies(data);
        console.log(data)
    }

    return (
        <Box>
            <Select
                isMulti
                name="colors"
                options={options}
                className="basic-multi-select"
                classNamePrefix="select"
                onChange={(e) => console.log(e)}
            />
            <TextField
                required
                label={`Prior Success`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'prior-success')}
            />
            <TextField
                required
                label={`Prior Failure`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'prior-failure')}
            />
            <TextField
                required
                label={`Max Rating`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'max_rating')}
            />
            <TextField
                required
                label={`Min Rating`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'min_rating')}
            />
            <TextField
                required
                label={`Uniform Threshold`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'uniform_threshold')}
            />
            <TextField
                required
                label={`TSPostDiff Threshold`}
                type="number"
                onChange={(e) => handleWeightChange(e, 'tspostdiff_thresh')}
            />
            <Box>
                <TextField
                    id="select-reward"
                    select
                    width="100px"
                    label="Select a reward"
                    onChange={(e) => handleWeightChange(e, 'outcome_variable_name')}
                >
                    {variables.map((variable, index) => (
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