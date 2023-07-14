import { React, useEffect } from 'react';
import { Typography, TextField, Button, Box, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';
import CommonMOOCletAttribute from './CommonMOOCletAttribute';

const CoefCovInput = (props) => {
    let mooclet = props.mooclet;
    let tree = props.tree;
    let sMooclets = props.sMooclets;

    const handleInputChange = (e, rowIndex, colIndex) => {
        const value = e.target.value;
        mooclet['parameters']['coef_cov'][rowIndex][colIndex] = Number(value);
        mooclet['parameters']['coef_cov'][colIndex][rowIndex] = Number(value);
        sMooclets(tree);
    };


    const renderMatrix = () => {
        return (mooclet['parameters']['coef_cov'] || []).map((row, rowIndex) => (
            <div key={rowIndex}>
                {row.map((cell, colIndex) => (
                    <input
                        key={colIndex}
                        value={cell}
                        type={"number"}
                        style={{ width: '4em', height: '4em' }}
                        onChange={e => handleInputChange(e, rowIndex, colIndex)}
                    />
                ))}
            </div>
        ));
    };

    return (
        <div>
            {renderMatrix()}
        </div>
    );
};



const CoefMeanInput = (props) => {
    let mooclet = props.mooclet;
    let tree = props.tree;
    let sMooclets = props.sMooclets;

    const handleInputChange = (e, index) => {
        const value = e.target.value;
        mooclet['parameters']['coef_mean'][index] = Number(value);
        sMooclets(tree);
    };


    const renderMatrix = () => {
        console.log(mooclet['parameters'])
        return (mooclet['parameters']['coef_mean'] || []).map((cell, index) => (
            <input
                key={index}
                value={cell}
                type={"number"}
                style={{ width: '4em', height: '4em' }}
                onChange={e => handleInputChange(e, index)}
            />
        ))
    }

    return (
        <div>
            {renderMatrix()}
        </div>
    );
};





function TSContextual(props) {
    let factors = props.factors;
    let variables = props.variables;
    let mooclets = props.mooclets;
    let sMooclets = props.sMooclets;
    let myId = props.myId;

    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);

    let regressionFormulaVariables = variables.concat(factors);

    let handleWeightChange = (event, name) => {
        mooclet['parameters'][name] = Number(event.target.value);
        sMooclets(tree)

    }

    const coefCovAddNewItem = () => {
        if (!mooclet['parameters']['coef_cov']) {
            mooclet['parameters']['coef_cov'] = [];
        }

        const n = mooclet['parameters']['coef_cov'].length;
        const expandedArray = Array(n + 1)
            .fill(null)
            .map(() => Array(n + 1).fill(0));
        if (n === 0) expandedArray[n][n] = 1; // TODO: Check if it's correct.
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                expandedArray[i][j] = mooclet['parameters']['coef_cov'][i][j];
            }
        }
        expandedArray[n][n] = 1;

        mooclet['parameters']['coef_cov'] = expandedArray;
        sMooclets(tree);
    };

    const coefCovAddIntercept = () => {
        if (!mooclet['parameters']['coef_cov']) {
            mooclet['parameters']['coef_cov'] = [];
        }

        const n = mooclet['parameters']['coef_cov'].length;
        const expandedArray = Array(n + 1)
            .fill(null)
            .map(() => Array(n + 1).fill(0));
        if (n === 0) expandedArray[n][n] = 1; // TODO: Check if it's correct.
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                expandedArray[i + 1][j + 1] = mooclet['parameters']['coef_cov'][i][j];
            }
        }

        expandedArray[0][0] = 1;

        mooclet['parameters']['coef_cov'] = expandedArray;
        sMooclets(tree);
    };


    const coefCovRemoveItem = rowIndex => {
        mooclet['parameters']['coef_cov'].splice(rowIndex, 1);
        mooclet['parameters']['coef_cov'].forEach(row => row.splice(rowIndex, 1));
        sMooclets(tree);
    };

    const coefMeanAddNewItem = () => {
        if (!mooclet['parameters']['coef_mean']) {
            mooclet['parameters']['coef_mean'] = [];
        }

        const expandedArray = mooclet['parameters']['coef_mean'].concat([0]);

        mooclet['parameters']['coef_mean'] = expandedArray;
        sMooclets(tree);
    };

    const coefMeanAddIntercept = () => {
        if (!mooclet['parameters']['coef_mean']) {
            mooclet['parameters']['coef_mean'] = [];
        }

        const expandedArray = [0].concat(mooclet['parameters']['coef_mean']);

        mooclet['parameters']['coef_mean'] = expandedArray;
        sMooclets(tree);
    };


    const coefMeanRemoveItem = index => {
        mooclet['parameters']['coef_mean'].splice(index, 1);
        sMooclets(tree);
    };

    const addFields = () => {
        let newfield = []
        let temp = [[]]
        if (mooclet['parameters']['regressionFormulaItems']) {
            temp = [...mooclet['parameters']['regressionFormulaItems'], newfield]
        }
        mooclet['parameters']['regressionFormulaItems'] = temp


        sMooclets(tree);
    }

    const removeFields = (index) => {
        mooclet['parameters']['regressionFormulaItems'].splice(index, 1);
        sMooclets(tree);
    }

    const handleRegressionFormulaItemPickup = (option, index) => {
        mooclet['parameters']["regressionFormulaItems"][index] = option.map((item) => item.value);

        let parameters = mooclet['parameters'];
        let deepCopy = JSON.parse(JSON.stringify(parameters));
        for(let i = 0; i < deepCopy['regressionFormulaItems'].length; i++) {
            if(deepCopy.regressionFormulaItems[i].length === 0) {
                
                parameters['regressionFormulaItems'].splice(i, 1);

                let coefIndex = deepCopy['include_intercept'] ? i + 1 : i;
                parameters['coef_cov'].splice(coefIndex, 1);
                parameters['coef_cov'].forEach(row => row.splice(coefIndex, 1));

                parameters['coef_mean'].splice(coefIndex, 1);
            }
        }
        sMooclets(tree)
    };

    const writeRegressionFormula = () => {
        let formula = "reward ~ "
        if (mooclet['parameters']['regressionFormulaItems']) {
            formula += mooclet['parameters']['regressionFormulaItems'].map((item) => item.join(" * ")).join(" + ")
        }
        return formula
    }


    useEffect(() => {
        // Initial parameters for TSContextual.
        if (!mooclet['parameters']['batch_size']) mooclet['parameters']['batch_size'] = 4
        if (!mooclet['parameters']['variance_a']) mooclet['parameters']['variance_a'] = 2
        if (!mooclet['parameters']['variance_b']) mooclet['parameters']['variance_b'] = 1
        if (!mooclet['parameters']['uniform_threshold']) mooclet['parameters']['uniform_threshold'] = 8
        if (!mooclet['parameters']['updatedPerMinute']) mooclet['parameters']['updatedPerMinute'] = 0
        if (!mooclet['parameters']['include_intercept']) mooclet['parameters']['include_intercept'] = false
        if (!mooclet['parameters']['individualLevelBatchSize']) mooclet['parameters']['individualLevelBatchSize'] = 1
        sMooclets(tree);

    }, []);



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
                value={mooclet['parameters']['updatedPerMinute'] || ''}
                onChange={(e) => handleWeightChange(e, 'updatedPerMinute')}
            />
            <Box>
                <FormControlLabel
                    control={<Checkbox checked={mooclet['parameters']['include_intercept'] || false} onChange={(e) => {
                        mooclet['parameters']['include_intercept'] = e.target.checked;
                        sMooclets(tree);
                        if (e.target.checked) {
                            coefCovAddIntercept();
                            coefMeanAddIntercept();
                        }
                        else {
                            coefCovRemoveItem(0);
                            coefMeanRemoveItem(0);
                        }
                    }} />}
                    label="Include Intercept"
                />
                <CommonMOOCletAttribute
                    mooclets={mooclets}
                    myId={myId}
                    sMooclets={sMooclets}
                />

                <FormControlLabel
                    control={<Checkbox checked={mooclet['parameters']['individualLevel'] || false} onChange={(e) => {
                        if (!mooclet['parameters']['individualLevelThreshold']) mooclet['parameters']['individualLevelThreshold'] = 0;
                        mooclet['parameters']['individualLevel'] = e.target.checked;
                        sMooclets(tree);
                    }} />}
                    label="Enable individual-level regression after receiving a certain number of feedbacks"
                />
                {mooclet['parameters']['individualLevel'] && <Box>
                    <p><mark>The individual level regressions will be turned on after receiving the following number of user feedbacks.</mark></p>
                    <TextField
                        sx={{ m: 1 }}
                        value={mooclet['parameters']['individualLevelThreshold']}
                        onChange={(e) => {
                            mooclet['parameters']['individualLevelThreshold'] = parseFloat(e.target.value);
                            sMooclets(tree);
                        }}
                        label={`Individual-level regression threshold`}
                        type="number"
                    />
                    <TextField
                        sx={{ m: 1 }}
                        value={mooclet['parameters']['individualLevelBatchSize']}
                        onChange={(e) => {
                            mooclet['parameters']['individualLevelBatchSize'] = parseFloat(e.target.value);
                            sMooclets(tree);
                        }}
                        label={`Individual-level regression batch size`}
                        type="number"
                    />
                </Box>}
            </Box>
            <Box sx={{ m: 1 }}>
                <Typography variant='h6'>Regression Formula Items</Typography>
                {mooclet['parameters']['regressionFormulaItems'] && mooclet['parameters']['regressionFormulaItems'].length > 0 && <mark><small>Current regression formula: {writeRegressionFormula()}</small></mark>}
                {mooclet['parameters']['regressionFormulaItems'] && mooclet['parameters']['regressionFormulaItems'].map((regressionFormulaItem, index) => {
                    return (
                        <Box key={index} margin="10px 0" style={{ position: "relative" }}>
                            <Select
                                isMulti
                                name="contextuals"
                                options={regressionFormulaVariables.map((option) => ({
                                    value: option,
                                    label: option
                                }))}
                                className="basic-multi-select"
                                classNamePrefix="select"
                                value={regressionFormulaItem.map(v => ({ label: v, value: v }))}
                                onChange={(option) => {
                                    handleRegressionFormulaItemPickup(option, index);
                                }}
                                styles={{
                                    // Fixes the overlapping problem of the component
                                    menu: provided => ({ ...provided, zIndex: 9999 })
                                }}
                            />
                            <Button onClick={() => {
                                removeFields(index);
                                coefCovRemoveItem(index);
                                coefMeanRemoveItem(index);
                            }
                            } variant="contained" sx={{ m: 1 }} color="error">Remove</Button>
                        </Box>
                    )
                })}

                <Button onClick={(e) => {
                    addFields();
                    coefCovAddNewItem();
                    coefMeanAddNewItem();
                }
                } variant="contained" color="primary" sx={{ m: 1 }}>Add a regression formula item</Button>

                <Box>
                    <Typography variant='h6'>Coefficient Covariance</Typography>
                    <small>The first is for the intercept if you have checked to include intercept.</small>
                    <CoefCovInput mooclet={mooclet} tree={tree} sMooclets={sMooclets} />
                </Box>

                <Box>
                    <Typography variant='h6'>Coefficient mean</Typography>
                    <small>The first is for the intercept if you have checked to include intercept.</small>
                    <CoefMeanInput mooclet={mooclet} tree={tree} sMooclets={sMooclets} />
                </Box>
            </Box>
        </Box >
    )
}


export default TSContextual;