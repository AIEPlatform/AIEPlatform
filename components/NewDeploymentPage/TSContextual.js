import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem } from '@mui/material';
import Select from 'react-select';

function TSContextual(props) {
    let versions = props.versions;
    let variables = props.variables;
    let mooclets = props.mooclets;
    let sMooclets = props.sMooclets;
    let myId = props.myId;

    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);

    let regressionFormulaVariables = variables.concat(versions);

    let handleWeightChange = (event, name) => {
        mooclet['parameters'][name] = event.target.value;
        sMooclets(tree)

    }

    const addFields = () => {
        let newfield = []
        let temp = [[]]
        if (mooclet['parameters']['regressionFormulaItems']) {
            temp = [...mooclet['parameters']['regressionFormulaItems'], newfield]
        }
        mooclet['parameters']['regressionFormulaItems'] = temp


        sMooclets(tree)
    }

    const removeFields = (index) => {
        let data = [...mooclet['parameters']['regressionFormulaItems']];
        data.splice(index, 1);
        sMooclets(tree);
    }

    const handleRegressionFormulaItemPickup = (option, index) => {
        mooclet['parameters']["regressionFormulaItems"][index] = option;
        sMooclets(tree)
    };


    return (
        <Box>
            <TextField
                sx={{ m: 1 }}
                required
                label={`Batch size`}
                type="number"
                value={mooclet['parameters']['batch_size'] || ''}
                onChange={(e) => handleWeightChange(e, 'batch_size')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Variance a`}
                type="number"
                value={mooclet['parameters']['variance_a'] || ''}
                onChange={(e) => handleWeightChange(e, 'variance_a')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Variance b`}
                type="number"
                value={mooclet['parameters']['variance_b'] || ''}
                onChange={(e) => handleWeightChange(e, 'variance_b')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Include_intercept`}
                type="number"
                value={mooclet['parameters']['include_intercept'] || ''}
                onChange={(e) => handleWeightChange(e, 'include_intercept')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Uniform Threshold`}
                type="number"
                value={mooclet['parameters']['uniform_threshold'] || ''}
                onChange={(e) => handleWeightChange(e, 'uniform_threshold')}
            />

            <TextField
                sx={{ m: 1 }}
                required
                label={`Posterior Update Frequency (in min)`}
                type="number"
                value={mooclet['parameters']['posterior_update_frequency'] || ''}
                onChange={(e) => handleWeightChange(e, 'posterior_update_frequency')}
            />
            <Box sx={{ m: 1 }}>
                <Typography variant='h6'>Regression Formula Items</Typography>

                {mooclet['parameters']['regressionFormulaItems'] && mooclet['parameters']['regressionFormulaItems'].map((regressionFormulaItem, index) => {
                    return (
                        <Box key={index} margin="10px 0" style={{ position: "relative" }}>
                            <Select
                                isMulti
                                name="contextuals"
                                options={regressionFormulaVariables}
                                getOptionValue={(option) => option.name}
                                getOptionLabel={(option) => option.name}
                                className="basic-multi-select"
                                classNamePrefix="select"
                                value={regressionFormulaItem}
                                onChange={(option) => {
                                    handleRegressionFormulaItemPickup(option, index);
                                }}
                                styles={{
                                    // Fixes the overlapping problem of the component
                                    menu: provided => ({ ...provided, zIndex: 9999 })
                                }}
                            />
                            <Button onClick={() => removeFields(index)} variant="contained" sx={{ m: 1 }} color="error">Remove</Button>
                        </Box>
                    )
                })}

                <Button onClick={(e) => addFields()} variant="contained" color="primary" sx={{ m: 1 }}>Add a regression formula item</Button>
            </Box>
        </Box >
    )
}


export default TSContextual;