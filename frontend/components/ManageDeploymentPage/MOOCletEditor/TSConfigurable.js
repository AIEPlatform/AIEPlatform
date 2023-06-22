import { React, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';
import CommonMOOCletAttribute from './CommonMOOCletAttribute';

function TSConfigurable(props) {
    let versions = props.versions;
    let mooclets = props.mooclets;
    let sMooclets = props.sMooclets;
    let myId = props.myId;

    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);

    console.log(mooclet)


    useEffect(() => {
        // Initial parameters for TSConfigurable.
        if (!mooclet['parameters']['prior']) {
            mooclet['parameters']['prior'] = { "successes": 1, "failures": 1 }
        }
        if (!mooclet['parameters']['batch_size']) mooclet['parameters']['batch_size'] = 4
        if (!mooclet['parameters']['max_rating']) mooclet['parameters']['max_rating'] = 1
        if (!mooclet['parameters']['min_rating']) mooclet['parameters']['min_rating'] = 0
        if (!mooclet['parameters']['uniform_threshold']) mooclet['parameters']['uniform_threshold'] = 8
        if (!mooclet['parameters']['tspostdiff_threshold']) mooclet['parameters']['tspostdiff_threshold'] = 0.1
        if (!mooclet['parameters']['current_posteriors']) mooclet['parameters']['current_posteriors'] = {}
        if (!mooclet['parameters']['epsilon']) mooclet['parameters']['epsilon'] = 0
        
        for(let version of versions) {
            if(!mooclet['parameters']['current_posteriors'][version['name']]) {
                mooclet['parameters']['current_posteriors'][version['name']] = {"successes": 1, "failures": 1}
            }
        }

        console.log(mooclet['parameters']['current_posteriors'])


        sMooclets(tree);

    }, []);
    if(mooclet['parameters']['prior']) {
        return (
            <Box>
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Epsilon`}
                    type="number"
                    value={mooclet['parameters']['epsilon'] || ''}
                    onChange={(e) => {
                        mooclet['parameters']['epsilon'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Prior Success`}
                    type="number"
                    value={mooclet['parameters']['prior']['successes']}
                    onChange={(e) => {
                        mooclet['parameters']['prior']['successes'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Prior Failure`}
                    type="number"
                    value={mooclet['parameters']['prior']['failures']}
                    onChange={(e) => {
                        mooclet['parameters']['prior']['failures'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Batch size`}
                    type="number"
                    value={mooclet['parameters']['batch_size']}
                    onChange={(e) => {
                        mooclet['parameters']['batch_size'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Max Rating`}
                    type="number"
                    value={mooclet['parameters']['max_rating']}
                    onChange={(e) => {
                        mooclet['parameters']['max_rating'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Min Rating`}
                    type="number"
                    value={mooclet['parameters']['min_rating']}
                    onChange={(e) => {
                        mooclet['parameters']['min_rating'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />

                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`Uniform Threshold`}
                    type="number"
                    value={mooclet['parameters']['uniform_threshold']}
                    onChange={(e) => {
                        mooclet['parameters']['uniform_threshold'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />

                <TextField
                    sx={{ m: 1 }}
                    required
                    label={`TSPostDiff Threshold`}
                    type="number"
                    value={mooclet['parameters']['tspostdiff_threshold']}
                    onChange={(e) => {
                        mooclet['parameters']['tspostdiff_threshold'] = parseFloat(e.target.value);
                        sMooclets(tree);
                    }}
                />
                <Box>
                    <CommonMOOCletAttribute
                        mooclets={mooclets}
                        myId={myId}
                        sMooclets={sMooclets}
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
                                    value={mooclet['parameters']['current_posteriors'][version['name']]['successes']}
                                    onChange={(e) => {
                                        mooclet['parameters']['current_posteriors'][version['name']]['successes'] = parseFloat(e.target.value);
                                        sMooclets(tree);
                                    }
                                    }
                                />
                                <TextField
                                    sx={{ m: 1 }}
                                    required
                                    key={version['name'] + 'failures'}
                                    label={`Failure`}
                                    type="number"
                                    value={mooclet['parameters']['current_posteriors'][version['name']]['failures']}
                                    onChange={(e) => {
                                        mooclet['parameters']['current_posteriors'][version['name']]['failures'] = parseFloat(e.target.value);
                                        sMooclets(tree);
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


export default TSConfigurable;