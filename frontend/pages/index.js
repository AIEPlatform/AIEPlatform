import * as React from 'react';
import { Container, Paper, Typography, Box, TextField } from "@mui/material";
import Select from 'react-select'
import Layout from '../components/layout';
import Head from 'next/head';

function ChooseMOOClet(props) {
    let MOOClets = props.MOOClets;
    let sSelectedMOOClet = props.sSelectedMOOClet;
    let sVariables = props.sVariables;
    let handleChooseMOOClet = (option) => {
        sSelectedMOOClet(MOOClets[option['value']]);

        fetch(`/apis/get_mooclet_information/${MOOClets[option['value']]['id']}`)
            .then(res => res.json())
            .then(response => {
                sVariables(response['data']['variables'])
            })

        props.sSelectedVariable(null);
    }

    return (
        <Select options={MOOClets.map((mooclet, index) => ({
            value: index,
            label: mooclet.name
        }))}
            onChange={(option) => {
                handleChooseMOOClet(option)
            }}
        />
    )
}


function ChooseVariable(props) {
    let variables = props.variables;
    let sSelectedVariable = props.sSelectedVariable;
    let handleChooseVariable = (option) => {
        console.log(option)
        sSelectedVariable(variables[option['value']][0]);
        console.log(variables[option['value']][0])
    }
    const options = variables.map((variable, index) => ({
        value: index,
        label: variable[0]
    }));
    return (
        <Select
            value={props.selectedVariable ? options[variables.indexOf(props.selectedVariable)] : null}
            options={options}
            onChange={(option) => {
                handleChooseVariable(option)
            }}
        />
    )
}


function DatasetDownloader(props) {

    const [MOOClets, sMOOClets] = React.useState([]);
    const [selectedMOOClet, sSelectedMOOClet] = React.useState(null);
    const [variables, sVariables] = React.useState([]);
    const [selectedVariable, sSelectedVariable] = React.useState(null);
    const [datasetDescription, sDatasetDescription] = React.useState("");
    React.useEffect(() => {
        fetch('/apis/get_mooclets')
            .then(res => res.json())
            .then(data => {
                if(data['status_code'] === 200)
                    sMOOClets(data['data']);
            })
    }, []);

    const downloadDataSet = () => {
        fetch(`/apis/analysis/data_downloader`, {
            method: "POST", // *GET, POST, PUT, DELETE, etc.
            mode: "cors", // no-cors, *cors, same-origin
            cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
            credentials: "same-origin", // include, *same-origin, omit
            headers: {
                "Content-Type": "application/json",
                // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            redirect: "follow", // manual, *follow, error
            referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify({
                mooclet_name: selectedMOOClet['name'],
                reward_variable_name: selectedVariable,
                dataset_description: datasetDescription
            }), // body data type must match "Content-Type" header
        })

            .then((response) => {
                if (response.status === 400) {
                    alert("Dataset Description already links to one dataset.")
                    return
                }
                if (response.status === 500) {
                    alert("Something is wrong. Please try again later.")
                    return
                }
                return response.blob()
            }
            )
            .then((blob) => {
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', 'data.csv');
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            })
            .catch((error) => {
                console.error(error);
            });
    }
    return (
        // MOOClet selector.
        <Layout>
            <Head><title>Dataset Downloader - DataArrow</title></Head>
            <Container>
            <p>If you don't see any mooclet, please visit this to sign up first: https://mooclet-dashboard.chenpan.ca/apis/signUpMOOCletToken/Token%(replace this with actually token)</p>
                <Typography>Please select a MOOClet from the following dropdown.</Typography>
                {MOOClets.length > 0 && <Paper
                    sx={{
                        p: 2,
                        display: 'flex',
                        flexDirection: 'column'
                    }}
                >
                    <TextField onChange={(e) => sDatasetDescription(e.target.value)} id="dataset-description" label="Dataset Description" variant="standard" style={{ marginBottom: '16px' }} />
                    <ChooseMOOClet
                        MOOClets={MOOClets}
                        sSelectedMOOClet={sSelectedMOOClet}
                        sVariables={sVariables}
                        sSelectedVariable={sSelectedVariable}
                    />

                    {variables.length > 0 && <ChooseVariable
                        variables={variables}
                        sSelectedVariable={sSelectedVariable}
                        selectedVariable={selectedVariable}
                    />}
                </Paper>}
                <Box>
                    {selectedMOOClet && selectedVariable && datasetDescription && <button onClick={downloadDataSet} style={{ marginTop: '16px' }}>
                        Download Dataset
                    </button>}
                </Box>
            </Container>
        </Layout>
    );
}

export default DatasetDownloader;
