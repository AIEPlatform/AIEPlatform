import { React, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Select from 'react-select'
import VersionEditor from '../components/MyMOOCletPage/VersionEditor';
import Layout from '../components/layout';
import Head from 'next/head';

function ChooseMOOClet(props) {
    let MOOClets = props.MOOClets;
    let sSelectedMOOClet = props.sSelectedMOOClet;
    let handleChooseMOOClet = (option) => {
        console.log(option)
        sSelectedMOOClet(MOOClets[option['value']]);
        // To get Versions, policies.
        fetch(`/apis/getMOOCletVersionsPolicies/${MOOClets[option['value']]['name']}`)
            .then(res => res.json())
            .then(response => {
                props.sVersions(response['versions']);
            })
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


function MyMOOClet() {
    const [MOOClets, sMOOClets] = useState(null);
    const [selectedMOOClet, sSelectedMOOClet] = useState(null);

    useEffect(() => {
        fetch('/apis/get_mooclets')
            .then(res => res.json())
            .then(data => {
                sMOOClets(data['data']);
            })
    }, []);

    const [versions, sVersions] = useState([
    ])

    return (
        <Layout>
            <Head><title>My MOOClets - MOOClet Dashboard</title></Head>
            <Container>
                {MOOClets === null && <Typography>Loading MOOClets...</Typography>}
                {MOOClets !== null && MOOClets.length == 0 && <Typography>You don't have any MOOClet yet.</Typography>}
                {MOOClets !== null && MOOClets.length > 0 && <><ChooseMOOClet
                    MOOClets={MOOClets}
                    sSelectedMOOClet={sSelectedMOOClet}
                    sVersions={sVersions}
                />
                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Versions</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <VersionEditor versions={versions} sVersions={sVersions} />
                        </AccordionDetails>
                    </Accordion></>}
            </Container>
        </Layout>
    );
}


export default MyMOOClet;