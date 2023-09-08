import { React, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';
import CommonAssignerAttribute from '../../CommonAssignerAttributes';


export function validate(props) {
    let assigner = props.assigner;
    let parameters = assigner['parameters'];
    let factors = props.factors;
    let variables = props.variables;
    let versions = props.versions;
    let existingVariables = props.existingVariables;

    if(!assigner['parameters']['current_posteriors']) {
        assigner['parameters']['current_posteriors'] = {};
    }
    
    for(let version of versions) {
        if(!assigner['parameters']['current_posteriors'][version['name']]) {
            assigner['parameters']['current_posteriors'][version['name']] = {"successes": 0, "failures": 0}
        }
    }

    for (const key in assigner['parameters']['current_posteriors']) {
        if (!versions.some(obj => obj['name'] === key)) {
          delete assigner['parameters']['current_posteriors'][key];
        }
      }
}

export const name = "Thompson Sampling";

export function main(props) {
    let versions = props.versions;
    let assigners = props.assigners;
    let sAssigners = props.sAssigners;
    let myId = props.myId;

    let tree = [...assigners];
    let assigner = tree.find(assigner => assigner.id === myId);

    useEffect(() => {
        // Initial parameters for TSConfigurable.
        if (!assigner['parameters']['prior']) {
            assigner['parameters']['prior'] = { "successes": 1, "failures": 1 }
        }
        if (!assigner['parameters']['batch_size']) assigner['parameters']['batch_size'] = 4
        if (!assigner['parameters']['max_rating']) assigner['parameters']['max_rating'] = 1
        if (!assigner['parameters']['min_rating']) assigner['parameters']['min_rating'] = 0
        if (!assigner['parameters']['uniform_threshold']) assigner['parameters']['uniform_threshold'] = 8
        if (!assigner['parameters']['tspostdiff_threshold']) assigner['parameters']['tspostdiff_threshold'] = 0.1
        if (!assigner['parameters']['current_posteriors']) assigner['parameters']['current_posteriors'] = {}
        if (!assigner['parameters']['epsilon']) assigner['parameters']['epsilon'] = 0
        
        for(let version of versions) {
            if(!assigner['parameters']['current_posteriors'][version['name']]) {
                assigner['parameters']['current_posteriors'][version['name']] = {"successes": 1, "failures": 1}
            }
        }

        sAssigners(tree);

    }, []);
    if(assigner['parameters']['prior']) {
        return (
            <Box>
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Epsilon`}
                    type="number"
                    value={assigner['parameters']['epsilon'] || ''}
                    onChange={(e) => {
                        assigner['parameters']['epsilon'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Prior Success`}
                    type="number"
                    value={assigner['parameters']['prior']['successes']}
                    onChange={(e) => {
                        assigner['parameters']['prior']['successes'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Prior Failure`}
                    type="number"
                    value={assigner['parameters']['prior']['failures']}
                    onChange={(e) => {
                        assigner['parameters']['prior']['failures'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Batch size`}
                    type="number"
                    value={assigner['parameters']['batch_size']}
                    onChange={(e) => {
                        assigner['parameters']['batch_size'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Max Rating`}
                    type="number"
                    value={assigner['parameters']['max_rating']}
                    onChange={(e) => {
                        assigner['parameters']['max_rating'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Min Rating`}
                    type="number"
                    value={assigner['parameters']['min_rating']}
                    onChange={(e) => {
                        assigner['parameters']['min_rating'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />

                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Uniform Threshold`}
                    type="number"
                    value={assigner['parameters']['uniform_threshold']}
                    onChange={(e) => {
                        assigner['parameters']['uniform_threshold'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />

                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`TSPostDiff Threshold`}
                    type="number"
                    value={assigner['parameters']['tspostdiff_threshold']}
                    onChange={(e) => {
                        assigner['parameters']['tspostdiff_threshold'] = parseFloat(e.target.value);
                        sAssigners(tree);
                    }}
                />
                <Box>
                    <CommonAssignerAttribute
                        assigners={assigners}
                        myId={myId}
                        sAssigners={sAssigners}
                    />
                </Box>
                <Box sx={{ m: 1 }}>
                    <Typography variant="h6">Posteriors</Typography>
                    {versions.map((version) => {
                        return (
                            <Box sx={{ m: 1 }}>
                                <Typography variant="h7" component="p">{version['name']}</Typography>
                                <TextField
                                    sx={{ m: 1 }}
                                    required
                                    key={version['name'] + 'successes'}
                                    label={`Success`}
                                    type="number"
                                    value={assigner['parameters']['current_posteriors'][version['name']]['successes']}
                                    onChange={(e) => {
                                        assigner['parameters']['current_posteriors'][version['name']]['successes'] = parseFloat(e.target.value);
                                        sAssigners(tree);
                                    }
                                    }
                                />
                                <TextField
                                    sx={{ m: 1 }}
                                    required
                                    key={version['name'] + 'failures'}
                                    label={`Failure`}
                                    type="number"
                                    value={assigner['parameters']['current_posteriors'][version['name']]['failures']}
                                    onChange={(e) => {
                                        assigner['parameters']['current_posteriors'][version['name']]['failures'] = parseFloat(e.target.value);
                                        sAssigners(tree);
                                    }
                                    }
                                />
                            </Box>
                        )
                    })}
                </Box>
            </Box >
        )
    }
}