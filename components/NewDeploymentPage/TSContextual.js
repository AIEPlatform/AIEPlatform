import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem } from '@mui/material';
import Select from 'react-select';
const options = [
    { value: 'ocean', label: 'Ocean' },
    { value: 'blue', label: 'Blue' }
]
function TSConfigurable(props) {
    let versions = props.versions;
    let variables = props.variables;
    let [regressionFormulaItems, sRegressionFormulaItems] = useState([]);
    let mooclets = props.mooclets;
    let sMooclets = props.sMooclets;
    let myId = props.myId;

    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);


    if('regressionFormulaItems' in mooclet['parameters']) {
        sRegressionFormulaItems(mooclet['parameters']['regressionFormulaItems'])
    }

    let regressionFormulaVariables = variables.concat(versions).map((variable, index) => {
        return { value: variable['name'], label: variable['name'] }
    })

    let handleWeightChange = (event, name) => {
        mooclet['parameters'][name] = event.target.value;
        sMooclets(tree)

    }

    const addFields = () => {
        let newfield = []
        sRegressionFormulaItems([...regressionFormulaItems, newfield])
    }

    const removeFields = (index) => {
        let data = [...regressionFormulaItems];
        data.splice(index, 1)
        sRegressionFormulaItems(data);
    }

    const handleRegressionFormulaItemPickup = (option, index) => {
        const filteredArrayB = variables.concat(versions).filter((elementB) =>
            option.some((elementA) => elementA.value === elementB.name)
        );

        if(!mooclet['parameters']['regressionFormulaItems']) {
            mooclet['parameters']['regressionFormulaItems'] = [];
        }
        let data = [...mooclet['parameters']["regressionFormulaItems"]];
        data[index] = filteredArrayB;
        // sRegressionFormulaItems(data);
        mooclet['parameters']["regressionFormulaItems"] = data;

        console.log(tree)
        //sMooclets(tree)
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
            <Box sx={{ m: 1 }}>
                <Typography variant='h6'>Regression Formula Items</Typography>

                {regressionFormulaItems.map((regressionFormulaItem, index) => {
                    return (
                        <Box key={index} margin="10px 0" style={{ position: "relative" }}>
                            <Select
                                isMulti
                                name="contextuals"
                                options={regressionFormulaVariables}
                                className="basic-multi-select"
                                classNamePrefix="select"
                                value={regressionFormulaItem.map((interactingVariable) => { return { value: interactingVariable['name'], label: interactingVariable['name'] } })}
                                onChange={(option) => {
                                    handleRegressionFormulaItemPickup(option, index);
                                }}
                                styles={{
                                    // Fixes the overlapping problem of the component
                                    menu: provided => ({ ...provided, zIndex: 9999 })
                                }}
                            />
                            <Button onClick={() => removeFields(index)} variant="contained" sx = {{m: 1}} color="error">Remove</Button>
                        </Box>
                    )
                })}

                <Button onClick={(e) => addFields()} variant="contained" color="primary" sx={{ m: 1 }}>Add a regression formula item</Button>
            </Box>
        </Box >
    )
}


export default TSConfigurable;