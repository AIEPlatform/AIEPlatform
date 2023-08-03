import { React, useContext, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import { UserContext } from "../contexts/UserContextWrapper";
import getConfig from 'next/config';
import Select from 'react-select';

const { publicRuntimeConfig } = getConfig();
const websiteName = publicRuntimeConfig.websiteName;
let missingDataOptions = [
    { value: 'Random', label: 'Random' },
    { value: 'Average', label: 'Average' },
    { value: 'Closest', label: 'Closest' },
    { value: 'Most Frequent', label: 'Most Frequent' },
    { value: 'Error', label: 'Error' }
];
function Variables() {
    const [variables, sVariables] = useState([]);

    const [studies, sStudies] = useState([]);

    const [selectedVariableIndex, sSelectedVariableIndex] = useState(null);

    const { userContext, sUserContext } = useContext(UserContext);
    useEffect(() => {
        if (userContext !== undefined && userContext === null) {
            window.location.href = "/Login";
        }
    }, [userContext]);

    useEffect(() => {
        fetch(`/apis/variables?showStudies=true`)
            .then(res => res.json())
            .then(response => {
                if (response['status_code'] === 200)
                    sVariables(response.data)
            })
            .catch(error => {
                alert("something is wrong with loading existing variables. Please try again later.");
            })
    }, []);



    if (userContext !== undefined && userContext !== null) {
        return (
            <Layout>
                <Head><title>Variables - {websiteName}</title></Head>
                <Container>
                    {/* Use react-native to allow users to select by variable name. When use select, change selectedVariable to that. */}

                    <Select
                        className="variables"
                        classNamePrefix="Variables"
                        isClearable={true}
                        isSearchable={true}
                        name="variables"
                        options={variables}
                        getOptionLabel={(option) => option.name}
                        getOptionValue={(option) => option.name}
                        onChange={(option) => {
                            if (option !== null) {
                                sSelectedVariableIndex(variables.findIndex((variable) => variable.name === option.name));
                            } else {
                                sSelectedVariableIndex(null);
                            }
                        }}
                        styles={{
                            // Fixes the overlapping problem of the component
                            menu: provided => ({ ...provided, zIndex: 9999 })
                        }}
                    />

                    <Divider />

                    {selectedVariableIndex !== null &&
                        <Paper sx={{
                            m: 1,
                            p: 2,
                            display: 'flex',
                            flexDirection: 'column'
                        }}>
                            <Typography variant="p" component="p" sx={{ mt: 1 }}>Type: {variables[selectedVariableIndex].type}</Typography>
                            {/* Print all studies that use this variable */}
                            <Typography variant="p" component="p" sx={{ mt: 1 }}>Studies: {variables[selectedVariableIndex].studies.join(", ")}</Typography>
                            <TextField
                                required
                                sx={{ mt: 1 }}
                                id="new-variable-name-input"
                                label="Min"
                                type="number"
                                value={variables[selectedVariableIndex].min}
                                onChange={(e) => {
                                    let newVariables = [...variables];
                                    newVariables[selectedVariableIndex].min = e.target.value;
                                    sVariables(newVariables);
                                }}
                                width="100%"
                                disabled
                            />
                            <TextField
                                required
                                sx={{ mt: 1 }}
                                id="new-variable-name-input"
                                label="Max"
                                type="number"
                                value={variables[selectedVariableIndex].max
                                }
                                onChange={(e) => {
                                    let newVariables = [...variables];
                                    newVariables[selectedVariableIndex].max = e.target.value;
                                    sVariables(newVariables);
                                }}
                                width="100%"
                                disabled
                            />
                            {variables[selectedVariableIndex].type === "text" &&
                                <TextField
                                    sx={{ mt: 1, mb: 1 }}
                                    id="variable-value-prompt"
                                    value={variables[selectedVariableIndex].variableValuePrompt}
                                    label="Prompt"
                                    multiline
                                    maxRows={10}
                                    onChange={(e) => {
                                        let newVariables = [...variables];
                                        newVariables[selectedVariableIndex].variableValuePrompt = e.target.value;
                                        sVariables(newVariables);
                                    }}
                                    InputLabelProps={{ shrink: true }}
                                />
                            }
                            <label htmlFor="variable-missing-option">Missing strategy:</label>
                            <Select
                                name="colors"
                                instanceId="variable-missing-option"
                                options={missingDataOptions}
                                getOptionLabel={(option) => option.label}
                                getOptionValue={(option) => option.value}
                                value = {{label: variables[selectedVariableIndex].missingStrategy, value: variables[selectedVariableIndex].missingStrategy}}
                                className="basic-multi-select"
                                classNamePrefix="select"
                                onChange={(option) => {
                                    let newVariables = [...variables];
                                    newVariables[selectedVariableIndex].missingStrategy = option.value;
                                    sVariables(newVariables);
                                }}
                                styles={{
                                    // Fixes the overlapping problem of the component
                                    menu: provided => ({ ...provided, zIndex: 9999 })
                                }}
                            />
                            {variables[selectedVariableIndex].studies.length > 0 && <Box sx={{mt: 2}}><mark>To delete a variable, please carefully review each relavant study, and remove the variable from those studies first!</mark></Box>}

                            <Button disabled = {variables[selectedVariableIndex].studies.length > 0}>Delete this variable</Button>
                            <Button >Update this variable</Button>
                        </Paper>
                    }

                </Container>

            </Layout>
        );
    }
}


export default Variables;