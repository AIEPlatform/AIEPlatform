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
        "policy": "UniformRandom",
        "parameters": {}, 
        "weight": 100
    }
]

function NewDeployment() {
    const [deploymentName, sDeploymentName] = useState("test2");
    const [deploymentDescription, sDeploymentDescription] = useState("test2 description");
    const [studyName, sStudyName] = useState("");
    const [variables, sVariables] = useState([
    ])

    const [versions, sVersions] = useState([
    ])

    const [mooclets, sMooclets] = useState(initialData);
    const handleDrop = (newTreeData) => sMooclets(newTreeData);

    const [moocletModalOpen, sMoocletModalOpen] = useState(false);

    const [idToEdit, sIdToEdit] = useState(null);

    const addMOOClet = () => {
        let newMOOClet = {
            "id": mooclets.length + 1,
            "parent": 1,
            "droppable": true,
            "isOpen": true,
            "isOpen": true,
            "text": `mooclet${mooclets.length + 1}`,
            "name": `mooclet${mooclets.length + 1}`,
            "policy": "UniformRandom",
            "parameters": {}, 
            "weight": 100
        }
        sMooclets([...mooclets, newMOOClet]);
    };

    const handleMOOCletModalClose = () => {
        sMoocletModalOpen(false);
        sIdToEdit(null);
    };

    const handleMOOCletWeightChange = (event, myId) => {
        let data = [...mooclets];
        let mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['weight'] = event.target.value;
        sMooclets(data);
    }

    const handleMOOCletRemove = (myId) => {
        let Tree = [...mooclets];
        function removeNode(id) {
            // Find the index of the node with the given id
            const nodeIndex = Tree.findIndex((node) => node.id === id);
          
            if (nodeIndex !== -1) {
              const node = Tree[nodeIndex];
              const childIds = getChildIds(node.id);
          
              // Remove the node from the Tree
              Tree.splice(nodeIndex, 1);
          
              // Remove the descendants recursively
              childIds.forEach(removeNode);
            }
          }
          
          function getChildIds(parentId) {
            return Tree
              .filter((node) => node.parent === parentId)
              .map((node) => node.id);
          }

        removeNode(myId);

        sMooclets(Tree);

        console.log(Tree)

    }


    const handleCreateStudy = () => {
        fetch('/apis/study', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "studyName": studyName,
                "description": deploymentDescription,
                "mooclets": mooclets, 
                "variables": variables,
                "versions": versions
        })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            alert("Study created successfully!");
        })
    };

    return (
        <Layout>
            <Head><title>New Deployment - DataArrow</title></Head>
            <Container>
                <Box>
                    <TextField sx = {{mb: 3}} label="Study name" value = {studyName} onChange={(e) => sStudyName(e.target.value)}></TextField>
                    <Accordion>
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls="panel1a-content"
                            id="panel1a-header"
                        >
                            <Typography variant='h6'>Variables</Typography>
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
                            <Typography variant='h6'>Versions</Typography>
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
                            <Typography variant='h6'>MOOClet Graph</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <DndProvider backend={MultiBackend} options={getBackendOptions()}>
                                {/* https://www.npmjs.com/package/@minoru/react-dnd-treeview */}
                                <Tree
                                    tree={mooclets}
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
                                            Weights: <input type="number" value={node.weight} onChange={(event) => handleMOOCletWeightChange(event, node.id)}></input> <button onClick={() => {
                                                handleMOOCletRemove(node.id)
                                            }}> Remove</button>
                                        </div>
                                    )}
                                />
                            </DndProvider>
                            <Button sx = {{m: 2}} variant="contained" onClick={addMOOClet}>Add a new MOOClet</Button>
                        </AccordionDetails>
                    </Accordion>
                    <Button sx = {{mt: 2}} variant="contained" onClick={handleCreateStudy} fullWidth>Create this study.</Button>
                </Box>
            </Container>

            <Modal
                open={moocletModalOpen}
                onClose={handleMOOCletModalClose}
                style={{overflow:'scroll', height: "80%", width: "80%", margin: "5% auto"}}
                
            >
                <Box style={{background: "white"}}>
                    <MOOCletEditor mooclets={mooclets} sMooclets={sMooclets} idToEdit={idToEdit} variables = {variables} versions={versions}></MOOCletEditor>
                </Box>
            </Modal>
        </Layout>
    );
}


export default NewDeployment;