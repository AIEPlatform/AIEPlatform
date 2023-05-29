import { React, useState } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import VariableEditor from '../components/NewDeploymentPage/VariableEditor';
import MoocletNameEditor from '../components/NewMOOCletPage/MoocletNameEditor';
import VersionEditor from '../components/NewMOOCletPage/VersionEditor';
import PolicyEditor from '../components/NewMOOCletPage/PolicyEditor';
import ChoosePolicyGroup from '../components/NewMOOCletPage/ChoosePolicyGroup';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Layout from '../components/layout';
import Head from 'next/head';
import Modal from '@mui/material/Modal';
import MOOCletEditor from '../components/NewDeploymentPage/MOOCletEditor';

import {
    Tree,
    getBackendOptions,
    MultiBackend,
} from "@minoru/react-dnd-treeview";
import { DndProvider } from "react-dnd";

let initialData = [
    {
        "id": 1,
        "parent": 0,
        "droppable": true,
        "isOpen": true,
        "text": "mooclet1",
        "name": "mooclet1",
        "policy": "choose_mooclet",
        "parameters": {}, 
        "weight": 100
    }
]

function NewDeployment() {
    const [deploymentName, sDeploymentName] = useState("test2");
    const [deploymentDescription, sDeploymentDescription] = useState("test2 description");
    const [studyName, sStudyName] = useState("test2 study");
    const [variables, sVariables] = useState([
    ])

    const [versions, sVersions] = useState([
    ])

    const [treeData, sTreeData] = useState(initialData);
    const handleDrop = (newTreeData) => sTreeData(newTreeData);

    const [moocletModalOpen, sMoocletModalOpen] = useState(false);

    const [idToEdit, sIdToEdit] = useState(null);

    const addMOOClet = () => {
        let newMOOClet = {
            "id": treeData.length + 1,
            "parent": 1,
            "droppable": true,
            "isOpen": true,
            "isOpen": true,
            "text": `mooclet${treeData.length + 1}`,
            "name": `mooclet${treeData.length + 1}`,
            "policy": "uniform_random",
            "parameters": {}, 
            "weight": 100
        }
        sTreeData([...treeData, newMOOClet]);
    };

    const handleMOOCletModalClose = () => {
        sMoocletModalOpen(false);
        sIdToEdit(null);
    };

    const handleMOOCletWeightChange = (event, myId) => {
        let data = [...treeData];
        let mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['weight'] = event.target.value;
        sTreeData(data);
    }



    return (
        <Layout>
            <Head><title>New Deployment - MOOClet Dashboard</title></Head>
            <Container>
                <Box>
                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Variables</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <VariableEditor selectedVariables={variables} sSelectedVariables={sVariables} />
                        </AccordionDetails>
                    </Accordion>

                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography>Versions</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <VersionEditor inputFields={versions} sInputFields={sVersions} />
                        </AccordionDetails>
                    </Accordion>
                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="mooclet-graph"
                            id="mooclet-graph"
                        >
                            <Typography>MOOClet Graph</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <DndProvider backend={MultiBackend} options={getBackendOptions()}>
                                {/* https://www.npmjs.com/package/@minoru/react-dnd-treeview */}
                                <Tree
                                    tree={treeData}
                                    rootId={0}
                                    onDrop={handleDrop}
                                    initialOpen={true}
                                    sort={false}
                                    render={(node, { depth, isOpen, onToggle }) => (
                                        <div style={{ marginLeft: depth * 10 }}>
                                            {node.droppable && (
                                                <span onClick={onToggle}>{isOpen ? "[-]" : "[+]"}</span>
                                            )}
                                            {node.name}: <button onClick={() => {
                                                sIdToEdit(node.id);
                                                sMoocletModalOpen(true);
                                            }}> Modify</button>
                                            Weights: <input type="number" value={node.weight} onChange={(event) => handleMOOCletWeightChange(event, node.id)}></input>
                                        </div>
                                    )}
                                />
                            </DndProvider>
                            <button onClick={addMOOClet}>add new mooclet</button>
                        </AccordionDetails>
                    </Accordion>
                </Box>
                <Button>Create this study.</Button>
            </Container>

            <Modal
                open={moocletModalOpen}
                onClose={handleMOOCletModalClose}
                style={{overflow:'scroll', height: "80%", width: "80%", margin: "5% auto"}}
                
            >
                <Box style={{background: "white"}}>
                    <MOOCletEditor treeData={treeData} sTreeData={sTreeData} idToEdit={idToEdit} variables = {variables} versions={versions}></MOOCletEditor>
                </Box>
            </Modal>
        </Layout>
    );
}


export default NewDeployment;