import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem } from '@mui/material';
import WeightedRandom from './WeightedRandom';
import TSConfigurable from './TSConfigurable';
import TSContextual from './TSContextual';
import Select from 'react-select';

const availablePolicies = [
    {
        value: 'uniform_random',
        label: 'Uniform Sample',
    },
    {
        value: 'weighted_random',
        label: 'Weighted Random',
    },
    {
        value: 'ts_configurable',
        label: 'TS Configurable',
    },
    {
        value: 'thompson_sampling_contextual',
        label: 'Thompson Sampling Contextual'
    }
];

function OnePolicyEditor(props) {
    let policies = props.policies;
    let [chosenPolicy, sChosenPolicy] = useState(null);
    let input = props.input;
    let index = props.index;
    let sPolicies = props.sPolicies;
    let versions = props.versions;
    let policyIndex = props.policyIndex;
    let variables = props.variables;

    let handlePolicyChange = (option) => {
        sChosenPolicy(option['value']);
        let data = [...policies];
        data[index]['type'] = option['value'];
        data[index]['parameter'] = {};
        sPolicies(data);
    }

    const removeFields = (index) => {
        let data = [...policies];
        data.splice(policyIndex, 1)
        sPolicies(data)
    }


    return (

        <Paper elevation={3} sx={{
            m: 3, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Box><Button sx={{ m: 1 }} onClick={() => removeFields(index)} variant="contained" color="error">Remove this policy</Button></Box>
            <Select
                name="colors"
                options={availablePolicies}
                className="basic-multi-select"
                classNamePrefix="select"
                onChange={(option) => handlePolicyChange(option)}
                styles={{
                    // Fixes the overlapping problem of the component
                    menu: provided => ({ ...provided, zIndex: 9999 })
                }}
            />
            {/* <Button onClick={() => removeFields(index)} variant="contained" style={{position: "absolute", bottom: "0", margin: "5px"}}>Remove</Button> */}

            {chosenPolicy === 'weighted_random' && <WeightedRandom versions={versions} policyIndex={policyIndex} policies={policies} sPolicies={sPolicies}></WeightedRandom>}
            {chosenPolicy === 'ts_configurable' && <TSConfigurable versions={versions} policyIndex={policyIndex} policies={policies} sPolicies={sPolicies} variables={variables}></TSConfigurable>}
            {chosenPolicy === 'thompson_sampling_contextual' && <TSContextual versions={versions} policyIndex={policyIndex} policies={policies} sPolicies={sPolicies} variables={variables}></TSContextual>}
        </Paper>
    )
}


export default OnePolicyEditor;

