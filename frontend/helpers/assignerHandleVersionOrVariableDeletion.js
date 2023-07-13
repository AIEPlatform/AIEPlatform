// To Policy Author, please note that you need to remove the version and variable from the assigner's policy, if your policy makes use of the version or variable that you are deleting.
function validifyStudy(study) {
    let modifiedStudy = {...study};

    for (const element of modifiedStudy.mooclets) {
        element.parameters = assignerHandleVersionOrVariableDeletion(element.policy, element.parameters, study.factors, study.variables, study.versions);
    }

    // For study versions. Need to remove the factor from the version if the factor is deleted, or add the factor if the factor is added.
    for(let factor of study.factors) {
        // check versionJSON of each version, and add the factor if it's not there.
        for(let version of study.versions) {
            if(!version.versionJSON.hasOwnProperty(factor)) {
                version.versionJSON[factor] = 0;
            }
        }
    }

    for(let version of study.versions) {
        // check versionJSON of each version, and remove the factor if it's not there.
        for(let factor of study.factors) {
            if(!version.versionJSON.hasOwnProperty(factor)) {
                delete version.versionJSON[factor];
            }
        }
    }



    return modifiedStudy;

}
function assignerHandleVersionOrVariableDeletion(policy, parameters, factors, variables, versions) {
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
        // Step 1: remove the item from the formula items (two for loop, one for version one for variable).
        // Step 2: remove the formula item that are empty. Reduce the corresponding parameters.

        // Can do: prompt the user it's very risky to do when an experiment is running. They may want to keep a copy of the previous matrices

        if(parameters['regressionFormulaItems'] === undefined) {
            return parameters;
        }
        let allVariables = factors.concat(variables);
    
        for(let i = 0; i < parameters['regressionFormulaItems'].length; i++) {
            parameters['regressionFormulaItems'][i] = parameters['regressionFormulaItems'][i].filter(item => {
                return allVariables.some(obj => obj === item);
              });

            
        }
        
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

            
        return parameters;
    }


    else if (policy === "TSConfigurable") {
        if(!parameters['current_posteriors']) {
            parameters['current_posteriors'] = {};
        }
        
        for(let version of versions) {
            console.log(version['name'])
            if(!parameters['current_posteriors'][version['name']]) {
                parameters['current_posteriors'][version['name']] = {"successes": 0, "failures": 0}
            }
        }

        for (const key in parameters['current_posteriors']) {
            if (!versions.some(obj => obj['name'] === key)) {
              delete parameters['current_posteriors'][key];
            }
          }

        console.log(parameters)
        return parameters;
    }
    else {
        return parameters;
    }
}

export default validifyStudy;