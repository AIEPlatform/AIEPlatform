import { React, useState } from 'react';
import { Typography, Paper, Button, Box, FormControl, NativeSelect } from '@mui/material';

function SimulationEditor(props) {
    // TODO: make this saved to DB.
    // TODO: handle when variable and version changes.
    let theStudy = props.study;
    let study = theStudy.name;
    let versions = theStudy.versions;
    let variables = theStudy.variables;
    let deployment = props.deploymentName;

    let [sampleSize, sSampleSize] = useState(100);
    let simulationSetting = theStudy.simulationSetting;
    let sSimulationSetting = props.sSimulationSetting;

    const [jsonData, setJsonData] = useState(null);

    const addNewSimulatedContextualEffect = () => {
        let newSimulationSetting = { ...simulationSetting };
        newSimulationSetting['contextualEffects'].push({
            "variable": null,
            "operator": "=", // TODO: add more operators.
            "value": null,
            "version": null,
            "effect": 0
        });
        sSimulationSetting(newSimulationSetting);
    }

    const handleEffectDelete = (index) => {
        let newSimulationSetting = { ...simulationSetting };
        newSimulationSetting['contextualEffects'].splice(index, 1);
        sSimulationSetting(newSimulationSetting);
    }

    const handleSaveSimulationSetting = () => {
        // An api call (put) /apis/experimentDesign/updateSimulationSetting with deployment and study.
        fetch('/apis/experimentDesign/updateSimulationSetting', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "deployment": deployment,
                "study": study,
                "simulationSetting": simulationSetting
            })
        }).then(response => {
            if (response.status === 200) {
                alert("Successfully updated the simulation setting!");
            } else {
                alert("Failed to update the simulation setting!");
            }
        }
        );
    }

    const handleRunSimulation = () => {
        // An api call (post) /apis/experimentDesign/runSimulation with deployment and study.
        fetch('/apis/experimentDesign/runSimulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "deployment": deployment,
                "study": study, 
                "sampleSize": sampleSize, 
                "simulationSetting": simulationSetting
            })
        }).then(response => response.json())
            .then(data => {
                if (data['status_code'] == 200) {
                    alert("Successfully ran the simulation!");
                }
                else {
                    alert(data.message);
                }
            }
            );
    }

    const handleStopSimulation = () => {
        // A PUT call
        fetch('/apis/experimentDesign/stopSimulation', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "deployment": deployment,
                "study": study
            })
        }).then(response => {
            if (response.status === 200) {
                alert("Successfully stopped the simulation!");
            } else {
                alert("Failed to stop the simulation!");
            }
        }
        );
    }

    const contextualEffectEditor = (contextualEffect, index) => {
        //write something like this: When a user is assigned to a version (which is an html select to choose a version), if the contextual (which is an html select to choose a variable) equals to (an input box for numbers), the reward probability is affected by (an input box for numbers).
        return (
            <Box sx={{ mt: 2 }} key={index}>
                <Box variant="body1">When a user is assigned to
                    <FormControl>
                        <NativeSelect
                            sx={{ ml: 1, mr: 1 }}
                            value={contextualEffect['version'] || ""}
                            onChange={(event) => {
                                let newSimulationSetting = { ...simulationSetting };
                                newSimulationSetting['contextualEffects'][index]['version'] = event.target.value;
                                sSimulationSetting(newSimulationSetting);

                            }}
                        >
                            <option value="">-- Select a version --</option>
                            {versions.map(version => {
                                return (
                                    <option value={version['name']} key={version['name']}>{version['name']}</option>
                                )
                            }
                            )}
                        </NativeSelect>
                    </FormControl>
                    , if <FormControl><NativeSelect
                        sx={{ ml: 1, mr: 1 }}
                        value={contextualEffect['variable'] || ""}
                        onChange={(event) => {
                            let newSimulationSetting = { ...simulationSetting };
                            newSimulationSetting['contextualEffects'][index]['variable'] = event.target.value;
                            sSimulationSetting(newSimulationSetting);
                        }}
                    >
                        <option value="">-- Select a variable --</option>
                        {variables.map(variable => {
                            return (
                                <option value={variable} key={variable}>{variable}</option>
                            )
                        }
                        )}
                    </NativeSelect>
                    </FormControl> equals to <input type="number" value={contextualEffect['value'] || ""} onChange={(event) => {
                        let newSimulationSetting = { ...simulationSetting };
                        newSimulationSetting['contextualEffects'][index]['value'] = event.target.value;
                        sSimulationSetting(newSimulationSetting);
                    }}></input>, the reward probability is affected by <input type="number" value={contextualEffect['effect' || 0]} onChange={(event) => {
                        let newSimulationSetting = { ...simulationSetting };
                        newSimulationSetting['contextualEffects'][index]['effect'] = event.target.value;
                        sSimulationSetting(newSimulationSetting);
                    }}></input>. <button onClick={() => handleEffectDelete(index)}>Click here if I want to remove this effect</button></Box>
            </Box>
        )
    }

    const exportToJson = () => {
        const jsonData = JSON.stringify(simulationSetting);
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
    
        const a = document.createElement('a');
        a.href = url;
        a.download = 'simulationSetting.json';
        a.click();
    
        URL.revokeObjectURL(url);
      };

    const importToJson = () => {
        
    }


    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
    
          reader.onload = (event) => {
            try {
              const parsedData = JSON.parse(event.target.result);
              setJsonData(parsedData);
              console.log(parsedData)
              sSimulationSetting(parsedData)
            } catch (error) {
              console.error('Error parsing JSON:', error);
            }
          };
    
          reader.readAsText(file);
        }
      };

    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {/* let's do the base reward probability first. */}
            <Box sx={{ mt: 2 }}>
                <mark>The simulator is now limited to binary reward, and uniform reward distribution!</mark>
                <Typography variant="body1">How many days this simulation have? (the simulated data will be splited evenly) <input type="number" value={simulationSetting['numDays'] || 5} onChange={(event) => {
                    let newSimulationSetting = { ...simulationSetting };
                    newSimulationSetting['numDays'] = event.target.value;
                    sSimulationSetting(newSimulationSetting);
                }}></input></Typography>
                <Typography variant="h6">Base Reward Probability</Typography>
                {versions.map(version => {
                    return (
                        // for each version, write something like this: Regardless of the contextual, the probability a user assigned to {version['name']} is ____ (this is an input box).
                        <Box sx={{ mt: 2 }} key={version['name']}>
                            <Typography variant="body1">Regardless of the contextual, the probability a user assigned to {version['name']} gives a positive reward is <input type="number" value={simulationSetting['baseReward'][version['name']] || 0.5} onChange={(event) => {
                                let newSimulationSetting = { ...simulationSetting };
                                newSimulationSetting['baseReward'][version['name']] = event.target.value;
                                sSimulationSetting(newSimulationSetting);
                            }}></input></Typography>
                        </Box>
                    )
                })}
                <Typography variant="h6">Contextual Effects {simulationSetting['contextualEffects'].length}</Typography>
                {simulationSetting['contextualEffects'].map((contextualEffect, index) => {
                    return contextualEffectEditor(contextualEffect, index);
                })}
                <Button variant="contained" sx={{ mt: 2 }} onClick={addNewSimulatedContextualEffect}>Add a new simulated contextual effect</Button>

            </Box>
            <Box sx={{ m: "auto", mt: 2 }}><Button onClick={handleRunSimulation} variant="outlined">Run Simulations</Button> with <input type="number" value={sampleSize} onChange={(event) => {
                sSampleSize(event.target.value);
            }}></input> samples</Box>
            <Box sx={{ m: "auto", mt: 2 }}>
                <Button sx={{ mr: 2}} onClick={handleSaveSimulationSetting} variant="outlined">Save</Button>
                <Button sx={{ }} onClick={handleStopSimulation} variant="outlined" color="error">Stop Simulation</Button>
                <button onClick={exportToJson}>Export Simulation Setting</button>
                <div>
                <input
                    type="file"
                    accept=".json"
                    onChange={handleFileChange}
                />
                {jsonData && (
                    <div>
                    <h2>Parsed JSON Data:</h2>
                    <pre>{JSON.stringify(jsonData, null, 2)}</pre>
                    </div>
                )}
                </div>
            </Box>
        </Paper>
    )
}


export default SimulationEditor;