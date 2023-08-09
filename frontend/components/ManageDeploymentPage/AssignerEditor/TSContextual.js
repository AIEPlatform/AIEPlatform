import { React, useEffect, useState } from 'react';
import { Typography, TextField, Button, Box, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';
import CommonAssignerAttribute from './CommonAssignerAttribute';

const CoefCovInput = (props) => {
    let assigner = props.assigner;
    let tree = props.tree;
    let sAssigners = props.sAssigners;

    const handleInputChange = (e, rowIndex, colIndex) => {
        const value = e.target.value;
        assigner['parameters']['coef_cov'][rowIndex][colIndex] = value;
        assigner['parameters']['coef_cov'][colIndex][rowIndex] = value;
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
        assigner['parameters']['coef_mean'][index] = value;
        sAssigners(tree);
    };


    const renderMatrix = () => {
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

    let existingVariables = props.existingVariables;


    let [newItem, sNewItem] = useState([]);

    let handleWeightChange = (event, name) => {
        assigner['parameters'][name] = event.target.value;
        sAssigners(tree)

    }

    const coefCovAddNewItem = (newItem) => {
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

    const coefMeanAddNewItem = (newItem) => {
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

    const calculateFormulateItemSize = (item) => {

        let merged = item.map((item) => {
            let found = existingVariables.find((variable) => variable.name === item.value);
            return { ...item, ...found };
        });
        let size = 1;
        merged.forEach((item) => {
            if (item.type === 'categorical') {
                size *= item.max - item.min + 1;
            }
        });
        return size;
    }

    const addRegressionFormulaItem = () => {
        // newItem is an array like 0: {value: 'job', label: 'job'} 1: {value: 'factor1', label: 'factor1'}.
        // Merge this array with existingVariables based on value, so we know the categorical or not, and the min and max.
        let sizeOfNewItems = calculateFormulateItemSize(newItem);
        let regressionFormulaItem = newItem.map((item) => item.value);

        let temp = [[]]

        if(!assigner['parameters']['regressionFormulaItems']){
            assigner['parameters']['regressionFormulaItems'] = [];
        }
        if (assigner['parameters']['regressionFormulaItems']) {
            temp = [...assigner['parameters']['regressionFormulaItems'], regressionFormulaItem]
        }
        assigner['parameters']['regressionFormulaItems'] = temp

        sAssigners(tree);

        // coefCovAddNewItem();
        // coefMeanAddNewItem();
        sNewItem([]);
    }

    const removeFields = (index) => {
        assigner['parameters']['regressionFormulaItems'].splice(index, 1);
        sAssigners(tree);
    }

    const handleRegressionFormulaItemPickup = (option, index) => {
        assigner['parameters']["regressionFormulaItems"][index] = option.map((item) => item.value);


        // check if the option is categorical or not.
        let isCategorical = false

        let parameters = assigner['parameters'];
        let deepCopy = JSON.parse(JSON.stringify(parameters));


        for (let i = 0; i < deepCopy['regressionFormulaItems'].length; i++) {
            if (deepCopy.regressionFormulaItems[i].length === 0) {

                parameters['regressionFormulaItems'].splice(i, 1);

                let coefIndex = deepCopy['include_intercept'] ? i + 1 : i;
                parameters['coef_cov'].splice(coefIndex, 1);
                parameters['coef_cov'].forEach(row => row.splice(coefIndex, 1));

                parameters['coef_mean'].splice(coefIndex, 1);
            }
        }
        sAssigners(tree)
    };

    function generateCombinations(arrays) {
        if (arrays.length === 0) {
          return [[]];
        }
      
        const firstArray = arrays[0];
        const restArrays = arrays.slice(1);
        const combinationsWithoutFirst = generateCombinations(restArrays);
      
        const result = [];
      
        for (const element of firstArray) {
          for (const combination of combinationsWithoutFirst) {
            result.push([element, ...combination]);
          }
        }
      
        return result;
      }

    const writeRegressionFormula = () => {
        let formula = "reward ~ "
        if (assigner['parameters']['regressionFormulaItems']) {

            let expandedFormulaItems = [];

            for (let i = 0; i < assigner['parameters']['regressionFormulaItems'].length; i++) {
                let item = assigner['parameters']['regressionFormulaItems'][i];
                let merged = item.map((item) => {
                    let found = existingVariables.find((variable) => variable.name === item);
                    return { item, ...found };
                });
                let expandedItem = [];
                merged.forEach((item) => {
                    if (item.type === 'categorical') {
                        let temp = [];
                        for (let i = item.min; i <= item.max; i++) {
                            temp.push(`${item.name}::${i}`);
                        }
                        expandedItem.push(temp);
                    }
                    else {
                        expandedItem.push([item.item]);
                    }
                });
                console.log(generateCombinations(expandedItem))
                expandedFormulaItems = expandedFormulaItems.concat(generateCombinations(expandedItem));
            }

            console.log(expandedFormulaItems)
            


            formula += expandedFormulaItems.map((item) => {
                // need to check if any of the item is categorical or not.
                // item is like ['job', 'nonCategorical']. let's say job is categorical.
                // Then we need to expand the item to ['job::1', 'job::2', ..., nonCategorical], depending on the min and max of job.
                return item.join(" * ")
            }).join(" + ")
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
                                isDisabled={true}
                                styles={{
                                    // Fixes the overlapping problem of the component
                                    menu: provided => ({ ...provided, zIndex: 9999 })
                                }}
                            />
                            <Button onClick={() => {
                                removeFields(index);
                                // coefCovRemoveItem(index);
                                // coefMeanRemoveItem(index);
                            }
                            } variant="contained" sx={{ m: 1 }} color="error">Remove</Button>
                        </Box>
                    )
                })}


                <Select
                    isMulti
                    name="contextuals"
                    options={regressionFormulaVariables.map((option) => ({
                        value: option,
                        label: option
                    }))}
                    className="basic-multi-select"
                    classNamePrefix="select"
                    value={newItem}
                    onChange={(e) => {
                        sNewItem(e);
                    }}
                    styles={{
                        // Fixes the overlapping problem of the component
                        menu: provided => ({ ...provided, zIndex: 9999 })
                    }}
                />

                <Button onClick={(e) => {
                    addRegressionFormulaItem();
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