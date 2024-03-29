// To Policy Author, please note that you need to remove the version and variable from the assigner's policy, if your policy makes use of the version or variable that you are deleting.

//calculateFormulateItemSize, coefCovRemoveItem, and coefMeanRemoveItem are helper functions from ../components/ManageDeploymentPage/AssignerEditor/TSCHelper.js

import {calculateFormulateItemSize, removeItemsFromSymmetricMatrix, coefCovRemoveItem} from './TSContextualHelpers';

function validifyStudy(study, existingVariables) {
    let modifiedStudy = {...study};


    // We want to make sure that the factorss & versions are on the same page.
    // 1. remove factors from version json if the factor is deleted.
    // 2. Auto initialize the factor in version json if the factor is added.

    for(let factor of study.factors) {
        // check versionJSON of each version, and add the factor if it's not there.
        for(let version of study.versions) {
            if(!version.versionJSON[factor]) {
                version.versionJSON[factor] = 0;
            }
        }
    }

    for(let version of study.versions) {
        // check versionJSON of each version, and remove the factor if it's not there.

        for(let factor in version.versionJSON) {
            if(!study.factors.includes(factor)) {
                delete version.versionJSON[factor];
            }
        }
    }
    // Validify the simulation setting.
    if(modifiedStudy.simulationSetting) {
        // first, add version or remove version to Base Reward Probability.
        // baseReward is a dict. I want to add a key-value from study.versions if the key not exist in baseReward.
        // Then, I want to remove the key-value from baseReward if the key not exist in study.versions.
        for(let version of study.versions) {
            if(!modifiedStudy.simulationSetting.baseReward.hasOwnProperty(version.name)) {
                modifiedStudy.simulationSetting.baseReward[version.name] = 0.5;
            }
        }

        for(let version in study.simulationSetting.baseReward) {
            if(!study.versions.some(obj => obj.name === version)) {
                delete modifiedStudy.simulationSetting.baseReward[version];
            }
        }

        // NEXT! remove contextual effects whose version or variable is not in the study.

        for(let i = 0; i < modifiedStudy.simulationSetting.contextualEffects.length; i++) {
            let contextualEffect = modifiedStudy.simulationSetting.contextualEffects[i];
            if(!study.versions.some(obj => obj.name === contextualEffect.version)) {
                //remove by index
                modifiedStudy.simulationSetting.contextualEffects.splice(i, 1);
            }
            if(!study.variables.some(obj => obj.name === contextualEffect.variable)) {
                modifiedStudy.simulationSetting.contextualEffects.splice(i, 1);
            }
        }
    }


    for (const element of modifiedStudy.assigners) {
        element.parameters = assignerHandleVersionOrVariableDeletion(element.policy, element.parameters, study.factors, study.variables, study.versions, existingVariables);
    }



    return modifiedStudy;

}
function assignerHandleVersionOrVariableDeletion(policy, parameters, factors, variables, versions, existingVariables) {
    if(policy === "UniformRandom") {
        return parameters;
    }
    else if (policy === "WeightedRandom") {
        for (const key in parameters) {
            if (!versions.some(obj => obj['name'] === key)) {
              delete parameters[key];
            }
          }
        return parameters;
    }
    else if (policy === "ThompsonSamplingContextual") {

        let original = JSON.parse(JSON.stringify(parameters));
        // Step 1: remove the item from the formula items (two for loop, one for version one for variable).
        // Step 2: remove the formula item that are empty. Reduce the corresponding parameters.

        // Can do: prompt the user it's very risky to do when an experiment is running. They may want to keep a copy of the previous matrices

        if(parameters['regressionFormulaItems'] === undefined) {
            return parameters;
        }
        let allVariables = factors.concat(variables);

        // if variables or versions changes, the regression formula items also need to be changed.
        for(let i = 0; i < parameters['regressionFormulaItems'].length; i++) {
            parameters['regressionFormulaItems'][i] = parameters['regressionFormulaItems'][i].filter(item => {
                return allVariables.some(obj => obj === item);
              });
        }

        // this is a little bit trick. because we may remove multiple items in the same time, we need to do it in a loop.
        let deepCopy = JSON.parse(JSON.stringify(parameters));
        for(let index = 0; index < deepCopy['regressionFormulaItems'].length; index++) {
            if(deepCopy.regressionFormulaItems[index].length === 0) {

                let startPoint = 0;
                for (let i = 0; i < index; i++) {
                    startPoint += calculateFormulateItemSize(existingVariables, original['regressionFormulaItems'][i]);
                }
        
                if(original['include_intercept']) {
                    startPoint += 1;
                }
                let sizeOfItem = calculateFormulateItemSize(existingVariables, original['regressionFormulaItems'][index]);
                let temp = removeItemsFromSymmetricMatrix(deepCopy['coef_cov'], startPoint, sizeOfItem);


                deepCopy['coef_cov'] = temp;
                deepCopy['coef_mean'].splice(startPoint, sizeOfItem);
                deepCopy['regressionFormulaItems'].splice(index, 1);


                original['regressionFormulaItems'].splice(index, 1); // This step is important. Otherwise, the index will be wrong.
                index--;
            }
        }

        return deepCopy;
    }


    else if (policy === "TSConfigurable") {
        if(!parameters['current_posteriors']) {
            parameters['current_posteriors'] = {};
        }
        
        for(let version of versions) {
            if(!parameters['current_posteriors'][version['name']]) {
                parameters['current_posteriors'][version['name']] = {"successes": 0, "failures": 0}
            }
        }

        for (const key in parameters['current_posteriors']) {
            if (!versions.some(obj => obj['name'] === key)) {
              delete parameters['current_posteriors'][key];
            }
          }
        return parameters;
    }
    else {
        return parameters;
    }
}

export default validifyStudy;