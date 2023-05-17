import * as React from 'react';
import { Container, Paper, Typography, Box } from "@mui/material";
import Select from 'react-select';
import Layout from '../components/layout';
import Head from 'next/head';

function ChooseDataset(props) {
    let datasets = props.datasets;
    let sSelectedDataset = props.sSelectedDataset;
    let handleChooseDataset = (option) => {
        sSelectedDataset(datasets[option['value']]);
    }
    const options = datasets.map((dataset, index) => ({
        value: index,
        label: dataset.datasetDescription
    }));
    return (
        <Select options={options} value={props.selectedDataset ? options[datasets.indexOf(props.selectedDataset)] : null}
            onChange={(option) => {
                handleChooseDataset(option)
            }}
        />
    )
}



function DatasetWorkshop(props) {

    const [datasets, sDatasets] = React.useState([]);
    const [selectedDataset, sSelectedDataset] = React.useState(null);

    const [csvFile, setCsvFile] = React.useState(null);

    const handleCsvUpload = (event) => {
        const file = event.target.files[0];
        setCsvFile(file);
    };

    const handleFileUpload = () => {
        const formData = new FormData();
        formData.append('csvFile', csvFile);
        formData.append('datasetDescription', selectedDataset['datasetDescription']);

        fetch('/apis/upload_local_dataset', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                console.log('File uploaded successfully');
            })
            .catch(error => {
                console.error('Error uploading file:', error);
            });
    };

    const downloadDataset = () => {
        fetch(`/apis/data_downloader/${selectedDataset['datasetDescription']}`)
            .then((response) => {
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

    const handleFileDelete = () => {
        fetch(`/apis/data_deletor/${selectedDataset['datasetDescription']}`, { method: 'DELETE' })
            .then((response) => {
                return response.json()
            }
            )
            .then((response) => {
                if (response.status_code === 200) {
                    sDatasets(response['data']);
                    sSelectedDataset(null);
                }
                else {
                    alert("something is wrong.")
                }
            })
            .catch((error) => {
                console.error(error);
            });
    }

    React.useEffect(() => {
        fetch('/apis/get_datasets')
            .then(res => res.json())
            .then(data => {
                if(data['status_code'] === 200)
                    sDatasets(data['data']);
            })
    }, []);

    return (
        // MOOClet selector.
        <Layout>
            <Head><title>Dataset Workshop - MOOClet Dashboard</title></Head>
            <Container>
                {datasets.length > 0 && <Typography>Please select a Dataset from the following dropdown.</Typography>}
                {datasets.length === 0 && <Typography>Please download a dataset at Dataset Downloader first.</Typography>}
                {datasets.length > 0 && <Paper
                    sx={{
                        p: 2,
                        display: 'flex',
                        flexDirection: 'column'
                    }}
                >
                    <ChooseDataset
                        datasets={datasets}
                        sSelectedDataset={sSelectedDataset}
                        selectedDataset={selectedDataset}
                    />
                </Paper>}
                <Box style={{ marginTop: '16px' }}>
                    {selectedDataset && <button onClick={downloadDataset}>
                        Download This Dataset (only do it if you don't have a local copy!)
                    </button>}
                </Box>
                {selectedDataset && <Box>
                    <Typography>ADVANCED: you can choose to work on the dataset locally, and re-upload the updated dataset, which will then replace the dataset in the cloud. KEEP IN MIND that this operation is not undoable!</Typography>
                    <label htmlFor="csv-upload">Upload CSV file:</label>
                    <input
                        id="csv-upload"
                        type="file"
                        accept=".csv"
                        onChange={handleCsvUpload}
                    />
                    {csvFile && <p>File selected: {csvFile.name}</p>}
                    {csvFile && <button onClick={handleFileUpload}>Upload</button>}
                </Box>}

                {selectedDataset && <Box style={{ marginTop: '16px' }}>
                    <Typography>BE CAREFUL! Click the following button to remove the dataset in the cloud.</Typography>
                    <button onClick={handleFileDelete}>Delete this dataset</button>
                </Box>}
            </Container>
        </Layout>
    );
}

export default DatasetWorkshop;
