import { React, useContext, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import Select from 'react-select';
import StudyEditor from '../components/ManageDeploymentPage/StudyEditor';
import { UserContext } from "../contexts/UserContextWrapper";


function ManageDeployment() {
    const [myDeployments, sMyDeployments] = useState([]);
    const [theStudies, sTheStudies] = useState([]);
    const [theStudy, sTheStudy] = useState(null);
    const [deploymentName, sDeploymentName] = useState(null);

    const { userContext, sUserContext } = useContext(UserContext);
    useEffect(() => {
        if (userContext !== undefined && userContext === null) {
            window.location.href = "/Login";
        }
    }, [userContext]);

    useEffect(() => {
        fetch('/apis/my_deployments')
            .then(response => response.json())
            .then(data => {
                sMyDeployments(data["my_deployments"]);
            });
    }, []);


    const [csvFile, setCsvFile] = useState(null);

    const handleCsvUpload = (event) => {
      const file = event.target.files[0];
      setCsvFile(file);
    };

    const handleSelectMyDeployment = (option) => {
        fetch(`/apis/the_studies/?deployment_id=${option["_id"]["$oid"]}`)
            .then(response => response.json())
            .then(data => {
                sTheStudies(data["studies"]);
                sDeploymentName(option['name'])
            });
    }

    const handleSelectStudy = (option) => {
        sTheStudy(option);
    }


    const handleFileUpload = () => {
        const formData = new FormData();
        formData.append('csvFile', csvFile);
        formData.append('datasetId', theDataset['_id']['$oid']);
    
        fetch('/apis/run_simulations', {
          method: 'PUT',
          body: formData
        })
          .then(response => response.json())
          .then(data => {
            if (data['status'] === 200) {
              window.location.reload();
            }
            else {
              alert("Error: " + data["message"]);
            }
          }
          )
          .catch(error => {
            console.error('Error uploading file:', error);
          });
      };

    if (userContext !== undefined && userContext !== null) {
        return (
            <Layout>
                <Head><title>Manage Deployment - DataArrow</title></Head>
                <Container>
                    <Box>
                        <Typography variant="p">Deployment: </Typography>
                        <Select
                            options={myDeployments}
                            getOptionLabel={(option) => option["name"]}
                            getOptionValue={(option) => option["_id"]["$oid"]}
                            onChange={(option) => handleSelectMyDeployment(option)}
                        />
                    </Box>


                    <Box>
                        <Typography variant="p">Study: </Typography>
                        <Select
                            options={theStudies}
                            getOptionLabel={(option) => option["name"]}
                            getOptionValue={(option) => option["_id"]["$oid"]}
                            value={theStudy}
                            onChange={(option) => handleSelectStudy(option)}
                        />
                    </Box>
                    {theStudy && <Box>
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
                </Container>
            </Layout>
        );
    }
}


export default ManageDeployment;