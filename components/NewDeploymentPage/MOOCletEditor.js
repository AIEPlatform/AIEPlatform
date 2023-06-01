import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Select from 'react-select';
import WeightedRandom from './WeightedRandom';
import TSContextual from './TSContextual';

const availablePolicies = [
    {
        value: 'uniform_random1',
        label: 'Uniform Sample',
    },
    {
        value: 'WeightedRandom',
        label: 'Weighted Random',
    },
    {
        value: 'TSConfigurable',
        label: 'TS Configurable',
    },
    {
        value: 'ThompsonSamplingContextual',
        label: 'Thompson Sampling Contextual'
    }
];


function MOOCletEditor(props) {
    let mooclets = props.mooclets;
    let myId = props.idToEdit;
    let sMooclets = props.sMooclets;
    let [chosenPolicy, sChosenPolicy] = useState(null);
    let versions = props.versions;
    let variables = props.variables;

    let mooclet = mooclets.find(mooclet => mooclet.id === myId);
    const handleMOOCletNameChange = (event) => {
        let data = [...mooclets];
        mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['name'] = event.target.value;
        mooclet['text'] = event.target.value;
        sMooclets(data);
    }


    let handlePolicyChange = (option) => {
        let data = [...mooclets];
        mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['policy'] = option.value;
        mooclet['parameters'] = {};
        sMooclets(data);
        // let data = [...policies];
        // data[index]['type'] = option['value'];
        // data[index]['parameter'] = {};
        // sPolicies(data);
    }

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Box sx={{ mt: 2 }}>
                Editing:
                <input type="text" name="name" value={mooclet.name} onChange={handleMOOCletNameChange} />
            </Box>

            <Box sx={{ mt: 2 }}>
                <Typography variant="h6">Policy</Typography>
                <Select
                    name="policies"
                    options={availablePolicies}
                    className="basic-multi-select"
                    classNamePrefix="select"
                    onChange={(option) => handlePolicyChange(option)}
                    value={availablePolicies.find(policy => policy.value === mooclet.policy)}
                    styles={{
                        // Fixes the overlapping problem of the component
                        menu: provided => ({ ...provided, zIndex: 9999 })
                    }}
                />
            </Box>

            <Box sx={{ mt: 2 }}>
                <Typography variant="h6">Policy Parameters</Typography>
                {mooclet.policy === 'UniformRandom' && <Typography>Uniform doesn't require a policy parameter!</Typography>}
                {mooclet.policy === 'WeightedRandom' && <WeightedRandom versions={versions} mooclets={mooclets} sMooclets = {sMooclets} myId={myId}></WeightedRandom>}
                {/* {mooclet.policy === 'ts_configurable' && <TSConfigurable versions={versions} policyIndex={policyIndex} policies={policies} sPolicies={sPolicies} variables={variables}></TSConfigurable>} */}
                {mooclet.policy === 'ThompsonSamplingContextual' && <TSContextual versions={versions} mooclets={mooclets} sMooclets = {sMooclets} myId={myId} variables={variables}></TSContextual>}
            </Box>
        </Paper>
    );
}


export default MOOCletEditor;