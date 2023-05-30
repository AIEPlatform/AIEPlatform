import * as React from 'react';
import { Container, Paper, Typography, Box, TextField } from "@mui/material";
import Select from 'react-select'
import Layout from '../components/layout';
import Head from 'next/head';

function DatasetDownloader(props) {

    const [MOOClets, sMOOClets] = React.useState([]);
    const [selectedMOOClets, sSelectedMOOClets] = React.useState([]);
    React.useEffect(() => {
        fetch('/apis/get_mooclets')
            .then(res => res.json())
            .then(data => {
                if (data['status_code'] === 200)
                    sMOOClets(data['data']);
            });

        const dataString = localStorage.getItem('MultipleDatasetDownloaderMOOClets');
        if (dataString) {
            // If data exists in local storage, parse it into an object
            const data = JSON.parse(dataString);
            sSelectedMOOClets(data);
            console.log(data)
        }
    }, []);

    const handleMOOCletPickUp = (option) => {
        sSelectedMOOClets(option);
        const dataString = JSON.stringify(option);
        localStorage.setItem('MultipleDatasetDownloaderMOOClets', dataString);
    }

    const downloadDataSets = async () => {
        const response = await fetch(`/apis/analysis/download_multiple_datasets`, {
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
                mooclet_names: selectedMOOClets.map(selectedMOOClet => { return selectedMOOClet['name'] }),
            }), // body data type must match "Content-Type" header
            timeout: 600000
        })

        if (response.ok) {
            const blob = await response.blob();

            // Create a temporary anchor element
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'dataframes.zip'; // Set the desired file name

            // Programmatically trigger a click event on the anchor element
            link.click();

            // Clean up: Revoke the object URL and remove the anchor element
            URL.revokeObjectURL(link.href);
            link.remove();
        }
}
return (
    // MOOClet selector.
    <Layout>
        <Head><title>Dataset Downloader - MOOClet Dashboard</title></Head>
        <Container>
            <Typography>Please select MOOClets from the following dropdown.</Typography>
            {
                MOOClets.length > 0 && <Select
                    isMulti
                    value={selectedMOOClets}
                    name="mooclets"
                    options={MOOClets}
                    onChange={handleMOOCletPickUp}
                    getOptionLabel={(option) => option.name}
                    getOptionValue={(option) => option.id}
                    className="basic-multi-select"
                    classNamePrefix="select"
                />
            }

            <Box>
                {selectedMOOClets.length > 0 && <button onClick={downloadDataSets} style={{ marginTop: '16px' }}>
                    Download Datasets
                </button>}
            </Box>
        </Container>
    </Layout>
);
}

export default DatasetDownloader;
