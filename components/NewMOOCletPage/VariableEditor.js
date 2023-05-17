import { React, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';
import Select from 'react-select';
function VariableEditor(props) {
    let selectedVariables = props.selectedVariables;
    let sSelectedVariables = props.sSelectedVariables;
    let [existingVariables, sExistingVariables] = useState([]);
    let [newVariable, sNewVariable] = useState("");

    const handleSelectChange = (option) => {

        sSelectedVariables(option.map((variable) => {
            return { name: variable['label'], index: variable['value'] }
        }))
    }

    useEffect(() => {
        fetch(`/apis/availableVariables`)
            .then(res => res.json())
            .then(response => {
                sExistingVariables(response.data)
                console.log(response.data)
            })
            .catch(error => {
                alert("something is wrong with loading existing variables. Please try again later.");
            })
    }, []);

    let handleCreateNewVariable = () => {
        fetch(`/apis/createNewVariable`, {
            method: "post",
            body: JSON.stringify({
                newVariableName: newVariable
            }),
            headers: {
                Accept: "application/json, text/plain, */*",
                "Content-Type": "application/json"
            }
        })
            .then(res => res.json())
            .then(response => {
                if (response.status_code == 200) {
                    sNewVariable("");
                    sExistingVariables(
                        [ // with a new array
                            ...existingVariables, // that contains all the old items
                            { name: newVariable } // and one new item at the end
                        ]
                    );

                    console.log([ // with a new array
                        ...existingVariables, // that contains all the old items
                        { name: newVariable } // and one new item at the end
                    ])
                    sSelectedVariables(
                        [
                            ...selectedVariables,
                            { name: newVariable, index: existingVariables.length }
                        ]
                    );
                }
                else {
                    alert(response.message);
                }
            })
    }
    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <Select
                isMulti
                name="colors"
                instanceId ="variable-select"
                options={existingVariables.map((variable, index) => {
                    return { value: index, label: variable['name'] }
                })}
                className="basic-multi-select"
                classNamePrefix="select"
                value={selectedVariables.map((variable) => { return { value: variable['index'], label: variable['name'] } })}
                onChange={(option) => handleSelectChange(option)}
                styles={{
                    // Fixes the overlapping problem of the component
                    menu: provided => ({ ...provided, zIndex: 9999 })
                }}
            />
            <Typography>If you want to create a new variable, please create it below (and this variable will be automatically linked to this mooclet). NOTE: Only binary reward is supported now.</Typography>
            <TextField
                required
                id="new-variable-name-input"
                label="New variable name"
                value={newVariable}
                onChange={(e) => sNewVariable(e.target.value)}
                width="100%"
            />
            <Button onClick={handleCreateNewVariable} variant="contained" color="primary" sx={{ m: 1 }}>Add a new reward</Button>
        </Paper>
    )
}


export default VariableEditor;