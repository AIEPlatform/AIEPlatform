import * as React from 'react';
import { Container, Paper, Typography, Box, TextField } from "@mui/material";
import Select from 'react-select'
import Layout from '../components/layout';
import Head from 'next/head';

function DatasetDownloader(props) {

    const [MOOClets, sMOOClets] = React.useState([]);
    const [selectedMOOClets, sSelectedMOOClets] = React.useState([]);
    const [email, sEmail] = React.useState("")
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
        const response = fetch(`/apis/analysis/download_multiple_datasets`, {
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
                email: email
            }), // body data type must match "Content-Type" header
        })

        alert("Please wait a little bit and check your email address for the link to download the datasets. (it may be in your spam!)")
    }
    return (
        // MOOClet selector.
        <Layout>
            <Head><title>Dataset Downloader - DataArrow</title></Head>
            <Container>

            <TextField
                    required
                    id="email-input"
                    label="Your email"
                    value={email}
                    onChange={(e) => sEmail(e.target.value)}
                    width="100%"
                />
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
