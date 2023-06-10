import { React, useState, useRef, use, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container, Input } from '@mui/material';
import VariableEditor from '../NewDeploymentPage/VariableEditor';
import VersionEditor from '../NewMOOCletPage/VersionEditor';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import Modal from '@mui/material/Modal';
import MOOCletEditor from '../NewDeploymentPage/MOOCletEditor';

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
        "text": "assigner1",
        "name": "assigner1",
        "policy": "UniformRandom",
        "parameters": {},
        "weight": 100
    }
]

function NewStudy(props) {
    const deploymentName = props.deploymentName;
    const [studyName, sStudyName] = useState("");
    const [variables, sVariables] = useState([
    ])

    const [versions, sVersions] = useState([
    ])

    const [mooclets, sMooclets] = useState(initialData);
    const handleDrop = (newTreeData) => sMooclets(newTreeData);

    const [moocletModalOpen, sMoocletModalOpen] = useState(false);

    const [idToEdit, sIdToEdit] = useState(null);


    const treeRef = useRef(null);
    const handleOpen = (nodeId) => treeRef.current.open(nodeId);

    const addMOOClet = () => {
        let newId = mooclets.length + 1;
        let newMOOClet = {
            "id": newId,
            "parent": 1,
            "droppable": true,
            "isOpen": true,
            "text": `assigner${newId}`,
            "name": `assigner${newId}`,
            "policy": "UniformRandom",
            "parameters": {},
            "weight": 100
        }
        sMooclets([...mooclets, newMOOClet]);

        handleOpen(newId);
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
                "deploymentName": deploymentName, // TODO: change to "deploymentId
                "studyName": studyName,
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

    useEffect(() => {
        handleOpen(1);
        // TODO: Think about how to open all the mooclets from cookies.
    });

    return (
        <Container sx={{mt: 4}}>
            <Box>
                <TextField sx={{ mb: 3 }} label="Study name" value={studyName} onChange={(e) => sStudyName(e.target.value)}></TextField>
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
                        <Typography variant='h6'>Design Graph</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <DndProvider backend={MultiBackend} options={getBackendOptions()}>
                            {/* https://www.npmjs.com/package/@minoru/react-dnd-treeview */}
                            <Tree
                                ref={treeRef}
                                tree={mooclets}
                                rootId={0}
                                onDrop={handleDrop}
                                initialOpen={true}
                                sort={false}
                                render={(node, { depth, isOpen, onToggle }) => (
                                    <Box style={{ marginLeft: depth * 10 }}>
                                        {node.droppable && (
                                            <span onClick={onToggle}>{isOpen ? "[-]" : "[+]"}</span>
                                        )}
                                        <Typography sx={{m: 0.5}}variant='span' component='strong'>{node.name}</Typography>
                                        <Typography sx={{m: 0.5}} variant='span'>Weight:</Typography>
                                        <Input className="assigner-weight-input" type="number" variant="standard" onChange={(event) => handleMOOCletWeightChange(event, node.id)} />
                                        <Button onClick={() => {
                                            sIdToEdit(node.id);
                                            sMoocletModalOpen(true);
                                        }}><EditIcon/></Button>
                                        
                                        <Button onClick={() => {
                                            handleMOOCletRemove(node.id)
                                        }} color = 'error'> <CloseIcon/></Button>
                                    </Box>
                                )}
                            />
                        </DndProvider>
                        <Button sx={{ m: 2 }} variant="contained" onClick={addMOOClet}>Add a new Assigner</Button>
                    </AccordionDetails>
                </Accordion>
                <Button sx={{ mt: 2 }} variant="contained" onClick={handleCreateStudy} fullWidth>Create this study.</Button>
            </Box>
            <Modal
                open={moocletModalOpen}
                onClose={handleMOOCletModalClose}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <MOOCletEditor mooclets={mooclets} sMooclets={sMooclets} idToEdit={idToEdit} variables={variables} versions={versions}></MOOCletEditor>
                </Box>
            </Modal>
        </Container>
    );
}


export default NewStudy;