import { React, use, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container, Checkbox, FormControlLabel } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import Select from 'react-select';
import NewStudy from '../components/ManageDeploymentPage/NewStudy'

function DataDownloader() {
    const [myDeployments, sMyDeployments] = useState([]);
    const [theStudies, sTheStudies] = useState([]);
    const [theStudy, sTheStudy] = useState(null);
    const [theDeployment, sTheDeployment] = useState(null);
    const [email, sEmail] = useState("");
    const [datasetName, sDatasetName] = useState("");
    useEffect(() => {
        fetch('/apis/my_deployments')
            .then(response => response.json())
            .then(data => {
                sMyDeployments(data["my_deployments"]);
            });
    }, []);

    const handleSelectMyDeployment = (option) => {
        sTheDeployment(option);
        fetch(`/apis/the_studies/?deployment_id=${option["_id"]["$oid"]}`)
            .then(response => response.json())
            .then(data => {
                sTheStudies(data["studies"]);
            });
    }

    const handleDownloadData = () => {
        alert("Thanks! Your dataset download request has been queued, you will receive an email when it succeeds or fails. Stay tuned!")
        fetch(`/apis/create_dataset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                study: theStudy["name"],
                email: email,
                deployment: theDeployment["name"], 
                datasetName: datasetName
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
            }
            );
    };

    return (
        <Layout>
            <Head><title>Manage Deployment - DataArrow</title></Head>
            <Container>
                <Box sx = {{mb: 3}}>
                    <Typography variant="p">Deployment: </Typography>
                    <Select 
                        options = {myDeployments}
                        getOptionLabel = {(option) => option["name"]}
                        getOptionValue = {(option) => option["_id"]["$oid"]}
                        onChange = {(option) => handleSelectMyDeployment(option)}
                    />
                </Box>


                <Box sx = {{mb: 3}}>
                    <Typography variant="p">Study: </Typography>
                    <Select 
                        options = {theStudies}
                        getOptionLabel = {(option) => option["name"]}
                        getOptionValue = {(option) => option["_id"]["$oid"]}
                        value={theStudy}
                        onChange = {(option) => sTheStudy(option)}
                    />
                </Box>

                <Box sx = {{mb: 3}}>
                    <Typography variant="p">Email: </Typography>
                    <Box><TextField value = {email} onChange = {(e) => sEmail(e.target.value)}></TextField></Box>
                </Box>

                <Box sx = {{mb: 3}}>
                    <Typography variant="p">Datataset Name: </Typography>
                    <Box><TextField value = {datasetName} onChange = {(e) => sDatasetName(e.target.value)}></TextField></Box>
                </Box>
                {theStudy && <Box><Button onClick={handleDownloadData}>Make a dataset snapshot to work on.</Button></Box>}
            </Container>
        </Layout>
    );
}


export default DataDownloader;