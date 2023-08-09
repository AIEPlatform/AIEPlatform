import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container, FormControl, InputLabel, Input } from '@mui/material';
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


function AssignerEditor(props) {
    let study = props.study;
    let assigners = props.assigners;
    let myId = props.idToEdit;
    let sAssigners = props.sAssigners;
    let versions = props.versions;
    let factors = props.factors;
    let variables = props.variables;
    let existingVariables = props.existingVariables;

    let assigner = assigners.find(assigner => assigner.id === myId);
    const handleAssignerNameChange = (event) => {
        let data = [...assigners];
        assigner = data.find(assigner => assigner.id === myId);
        assigner['name'] = event.target.value;
        assigner['text'] = event.target.value;
        sAssigners(data);
    }


    let handlePolicyChange = (option) => {
        let data = [...assigners];
        assigner = data.find(assigner => assigner.id === myId);
        assigner['policy'] = option.value;
        assigner['parameters'] = {};
        sAssigners(data);
    }

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Box sx={{ mt: 2 }}>
                <FormControl variant="standard">
                    <InputLabel htmlFor="input-with-icon-adornment">
                        Rename this assigner
                    </InputLabel>
                    <Input
                        id="input-with-icon-adornment"
                        value={assigner.name}
                        onChange={handleAssignerNameChange}
                    />
                </FormControl>
            </Box>

            <Box sx={{ mt: 2 }}>
                <Typography variant="h6">Policy</Typography>
                {(assigner.dbId === undefined || study['status'] === "reset") && <Select
                    name="policies"
                    options={availablePolicies}
                    className="basic-multi-select"
                    classNamePrefix="select"
                    onChange={(option) => handlePolicyChange(option)}
                    value={availablePolicies.find(policy => policy.value === assigner.policy)}
                    styles={{
                        // Fixes the overlapping problem of the component
                        menu: provided => ({ ...provided, zIndex: 9999 })
                    }}
                />}

                {assigner.dbId !== undefined && study['status'] !== "reset" && <Typography>{assigner.policy}</Typography>}
            </Box>

            <Box sx={{ mt: 2 }}>
                <Typography variant="h6">Policy Parameters</Typography>
                {assigner.policy === 'UniformRandom' && <UniformRandom versions={versions} assigners={assigners} sAssigners={sAssigners} myId={myId}>Uniform doesn't require a policy parameter!</UniformRandom>}
                {assigner.policy === 'WeightedRandom' && <WeightedRandom versions={versions} assigners={assigners} sAssigners={sAssigners} myId={myId}></WeightedRandom>}
                {assigner.policy === 'TSConfigurable' && <TSConfigurable versions={versions} factors={factors} assigners={assigners} sAssigners={sAssigners} myId={myId} variables={variables}></TSConfigurable>}
                {assigner.policy === 'ThompsonSamplingContextual' && <TSContextual existingVariables={existingVariables} factors={factors} assigners={assigners} sAssigners={sAssigners} myId={myId} variables={variables}></TSContextual>}
                {assigner.policy === 'GPT' && <GPT factors={factors} assigners={assigners} sAssigners={sAssigners} myId={myId} variables={variables}></GPT>}


            </Box>
        </Paper>
    );
}


export default AssignerEditor;