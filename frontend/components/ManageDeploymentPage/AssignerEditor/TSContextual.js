import { React, useEffect } from 'react';
import { Typography, TextField, Button, Box, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';
import CommonAssignerAttribute from './CommonAssignerAttribute';

const CoefCovInput = (props) => {
    let assigner = props.assigner;
    let tree = props.tree;
    let sAssigners = props.sAssigners;

    const handleInputChange = (e, rowIndex, colIndex) => {
        const value = e.target.value;
        assigner['parameters']['coef_cov'][rowIndex][colIndex] = Number(value);
        assigner['parameters']['coef_cov'][colIndex][rowIndex] = Number(value);
        sAssigners(tree);
    };


    const renderMatrix = () => {
        return (assigner['parameters']['coef_cov'] || []).map((row, rowIndex) => (
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
    let assigner = props.assigner;
    let tree = props.tree;
    let sAssigners = props.sAssigners;

    const handleInputChange = (e, index) => {
        const value = e.target.value;
        assigner['parameters']['coef_mean'][index] = Number(value);
        sAssigners(tree);
    };


    const renderMatrix = () => {
        console.log(assigner['parameters'])
        return (assigner['parameters']['coef_mean'] || []).map((cell, index) => (
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
    let assigners = props.assigners;
    let sAssigners = props.sAssigners;
    let myId = props.myId;

    let tree = [...assigners];
    let assigner = tree.find(assigner => assigner.id === myId);

    let regressionFormulaVariables = variables.concat(factors);

    let handleWeightChange = (event, name) => {
        assigner['parameters'][name] = Number(event.target.value);
        sAssigners(tree)

    }

    const coefCovAddNewItem = () => {
        if (!assigner['parameters']['coef_cov']) {
            assigner['parameters']['coef_cov'] = [];
        }

        const n = assigner['parameters']['coef_cov'].length;
        const expandedArray = Array(n + 1)
            .fill(null)
            .map(() => Array(n + 1).fill(0));
        if (n === 0) expandedArray[n][n] = 1; // TODO: Check if it's correct.
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                expandedArray[i][j] = assigner['parameters']['coef_cov'][i][j];
            }
        }
        expandedArray[n][n] = 1;

        assigner['parameters']['coef_cov'] = expandedArray;
        sAssigners(tree);
    };

    const coefCovAddIntercept = () => {
        if (!assigner['parameters']['coef_cov']) {
            assigner['parameters']['coef_cov'] = [];
        }

        const n = assigner['parameters']['coef_cov'].length;
        const expandedArray = Array(n + 1)
            .fill(null)
            .map(() => Array(n + 1).fill(0));
        if (n === 0) expandedArray[n][n] = 1; // TODO: Check if it's correct.
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                expandedArray[i + 1][j + 1] = assigner['parameters']['coef_cov'][i][j];
            }
        }

        expandedArray[0][0] = 1;

        assigner['parameters']['coef_cov'] = expandedArray;
        sAssigners(tree);
    };


    const coefCovRemoveItem = rowIndex => {
        assigner['parameters']['coef_cov'].splice(rowIndex, 1);
        assigner['parameters']['coef_cov'].forEach(row => row.splice(rowIndex, 1));
        sAssigners(tree);
    };

    const coefMeanAddNewItem = () => {
        if (!assigner['parameters']['coef_mean']) {
            assigner['parameters']['coef_mean'] = [];
        }

        const expandedArray = assigner['parameters']['coef_mean'].concat([0]);

        assigner['parameters']['coef_mean'] = expandedArray;
        sAssigners(tree);
    };

    const coefMeanAddIntercept = () => {
        if (!assigner['parameters']['coef_mean']) {
            assigner['parameters']['coef_mean'] = [];
        }

        const expandedArray = [0].concat(assigner['parameters']['coef_mean']);

        assigner['parameters']['coef_mean'] = expandedArray;
        sAssigners(tree);
    };


    const coefMeanRemoveItem = index => {
        assigner['parameters']['coef_mean'].splice(index, 1);
        sAssigners(tree);
    };

    const addFields = () => {
        let newfield = []
        let temp = [[]]
        if (assigner['parameters']['regressionFormulaItems']) {
            temp = [...assigner['parameters']['regressionFormulaItems'], newfield]
        }
        assigner['parameters']['regressionFormulaItems'] = temp


        sAssigners(tree);
    }

    const removeFields = (index) => {
        assigner['parameters']['regressionFormulaItems'].splice(index, 1);
        sAssigners(tree);
    }

    const handleRegressionFormulaItemPickup = (option, index) => {
        assigner['parameters']["regressionFormulaItems"][index] = option.map((item) => item.value);

        let parameters = assigner['parameters'];
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
        sAssigners(tree)
    };

    const writeRegressionFormula = () => {
        let formula = "reward ~ "
        if (assigner['parameters']['regressionFormulaItems']) {
            formula += assigner['parameters']['regressionFormulaItems'].map((item) => item.join(" * ")).join(" + ")
        }
        return formula
    }


    useEffect(() => {
        // Initial parameters for TSContextual.
        if (!assigner['parameters']['batch_size']) assigner['parameters']['batch_size'] = 4
        if (!assigner['parameters']['variance_a']) assigner['parameters']['variance_a'] = 2
        if (!assigner['parameters']['variance_b']) assigner['parameters']['variance_b'] = 1
        if (!assigner['parameters']['uniform_threshold']) assigner['parameters']['uniform_threshold'] = 8
        if (!assigner['parameters']['updatedPerMinute']) assigner['parameters']['updatedPerMinute'] = 0
        if (!assigner['parameters']['include_intercept']) assigner['parameters']['include_intercept'] = false
        if (!assigner['parameters']['individualLevelBatchSize']) assigner['parameters']['individualLevelBatchSize'] = 1
        sAssigners(tree);

    }, []);



    return (
        <Box>
            <TextField
                sx={{ m: 1 }}
                required
                label={`Batch size`}
                type="number"
                value={assigner['parameters']['batch_size'] || ''}
                onChange={(e) => handleWeightChange(e, 'batch_size')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Variance a`}
                type="number"
                value={assigner['parameters']['variance_a'] || ''}
                onChange={(e) => handleWeightChange(e, 'variance_a')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Variance b`}
                type="number"
                value={assigner['parameters']['variance_b'] || ''}
                onChange={(e) => handleWeightChange(e, 'variance_b')}
            />
            <TextField
                sx={{ m: 1 }}
                required
                label={`Uniform Threshold`}
                type="number"
                value={assigner['parameters']['uniform_threshold'] || ''}
                onChange={(e) => handleWeightChange(e, 'uniform_threshold')}
            />

            <TextField
                sx={{ m: 1 }}
                required
                label={`Posterior Update Frequency (in min)`}
                type="number"
                value={assigner['parameters']['updatedPerMinute'] || ''}
                onChange={(e) => handleWeightChange(e, 'updatedPerMinute')}
            />
            <Box>
                <FormControlLabel
                    control={<Checkbox checked={assigner['parameters']['include_intercept'] || false} onChange={(e) => {
                        assigner['parameters']['include_intercept'] = e.target.checked;
                        sAssigners(tree);
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
                <CommonAssignerAttribute
                    assigners={assigners}
                    myId={myId}
                    sAssigners={sAssigners}
                />

                <FormControlLabel
                    control={<Checkbox checked={assigner['parameters']['individualLevel'] || false} onChange={(e) => {
                        if (!assigner['parameters']['individualLevelThreshold']) assigner['parameters']['individualLevelThreshold'] = 0;
                        assigner['parameters']['individualLevel'] = e.target.checked;
                        sAssigners(tree);
                    }} />}
                    label="Enable individual-level regression after receiving a certain number of feedbacks"
                />
                {assigner['parameters']['individualLevel'] && <Box>
                    <p><mark>The individual level regressions will be turned on after receiving the following number of user feedbacks.</mark></p>
                    <TextField
                        sx={{ m: 1 }}
                        value={assigner['parameters']['individualLevelThreshold']}
                        onChange={(e) => {
                            assigner['parameters']['individualLevelThreshold'] = parseFloat(e.target.value);
                            sAssigners(tree);
                        }}
                        label={`Individual-level regression threshold`}
                        type="number"
                    />
                    <TextField
                        sx={{ m: 1 }}
                        value={assigner['parameters']['individualLevelBatchSize']}
                        onChange={(e) => {
                            assigner['parameters']['individualLevelBatchSize'] = parseFloat(e.target.value);
                            sAssigners(tree);
                        }}
                        label={`Individual-level regression batch size`}
                        type="number"
                    />
                </Box>}
            </Box>
            <Box sx={{ m: 1 }}>
                <Typography variant='h6'>Regression Formula Items</Typography>
                {assigner['parameters']['regressionFormulaItems'] && assigner['parameters']['regressionFormulaItems'].length > 0 && <mark><small>Current regression formula: {writeRegressionFormula()}</small></mark>}
                {assigner['parameters']['regressionFormulaItems'] && assigner['parameters']['regressionFormulaItems'].map((regressionFormulaItem, index) => {
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
                    <CoefCovInput assigner={assigner} tree={tree} sAssigners={sAssigners} />
                </Box>

                <Box>
                    <Typography variant='h6'>Coefficient mean</Typography>
                    <small>The first is for the intercept if you have checked to include intercept.</small>
                    <CoefMeanInput assigner={assigner} tree={tree} sAssigners={sAssigners} />
                </Box>
            </Box>
        </Box >
    )
}


export default TSContextual;