import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Select from 'react-select';
import WeightedRandom from './WeightedRandom';
import TSContextual from './TSContextual';
import TSConfigurable from './TSConfigurable'
import GPT from './GPT'
import UniformRandom from './UniformRandom';
const availablePolicies = [
    {
        value: 'UniformRandom',
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
    },
    {
        value: 'GPT',
        label: 'GPT'
    }
];


function MOOCletEditor(props) {
    let mooclets = props.mooclets;
    let myId = props.idToEdit;
    let sMooclets = props.sMooclets;
    let versions = props.versions;
    let factors = props.factors;
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
                {mooclet.dbId == undefined && <Select
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
                />}

                {mooclet.dbId !== undefined && <Typography>{mooclet.policy}</Typography>}
            </Box>

            <Box sx={{ mt: 2 }}>
                <Typography variant="h6">Policy Parameters</Typography>
                {mooclet.policy === 'UniformRandom' && <UniformRandom versions={versions} mooclets={mooclets} sMooclets={sMooclets} myId={myId}>Uniform doesn't require a policy parameter!</UniformRandom>}
                {mooclet.policy === 'WeightedRandom' && <WeightedRandom versions={versions} mooclets={mooclets} sMooclets={sMooclets} myId={myId}></WeightedRandom>}
                {mooclet.policy === 'TSConfigurable' && <TSConfigurable versions={versions} factors={factors} mooclets={mooclets} sMooclets={sMooclets} myId={myId} variables={variables}></TSConfigurable>}
                {mooclet.policy === 'ThompsonSamplingContextual' && <TSContextual factors={factors} mooclets={mooclets} sMooclets={sMooclets} myId={myId} variables={variables}></TSContextual>}
                {mooclet.policy === 'GPT' && <GPT factors={factors} mooclets={mooclets} sMooclets={sMooclets} myId={myId} variables={variables}></GPT>}

                
            </Box>
        </Paper>
    );
}


export default MOOCletEditor;