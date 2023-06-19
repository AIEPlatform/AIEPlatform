import { React, useState, useRef, use, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container, Input } from '@mui/material';
import VariableEditor from '../ManageDeploymentPage/VariableEditor';
import VersionFactorsEditor from './VersionFactorsEditor';
import VersionEditor from './VersionEditor';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import Modal from '@mui/material/Modal';
import MOOCletEditor from '../NewDeploymentPage/MOOCletEditor';
import RewardEditor from './RewardEditor';
import assignerHandleVersionOrVariableDeletion from '../../helpers/assignerHandleVersionOrVariableDeletion';
import APICard from './APICard';

import {
    Tree,
    getBackendOptions,
    MultiBackend,
} from "@minoru/react-dnd-treeview";
import { DndProvider } from "react-dnd";

function StudyEditor(props) {

    let theStudy = props.theStudy;

    let designGraph = [
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


    const [status, sStatus] = useState(0); // 0: loading, 1: new study, 2: existing study.
    const deploymentName = props.deploymentName;
    const [studyName, sStudyName] = useState("");
    const [variables, sVariables] = useState([]);
    const [versions, sVersions] = useState([]);
    const [factors, sFactors] = useState([]);
    const [existingFactors, sExistingFactors] = useState([]);
    const [mooclets, sMooclets] = useState(designGraph);
    const handleDrop = (newTreeData) => sMooclets(newTreeData);
    const [moocletModalOpen, sMoocletModalOpen] = useState(false);
    const [idToEdit, sIdToEdit] = useState(null);
    const treeRef = useRef(null);
    const handleOpen = (nodeId) => treeRef.current.open(nodeId);


    const [rewardInformation, sRewardInformation] = useState({
        "name": "reward", 
        "min": 0, 
        "max": 1
    });

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
                "versions": versions, 
                "factors": factors,
                "rewardInformation": rewardInformation
            })
        })
            .then(response => response.json())
            .then(data => {
                if(data['status'] == 200) {
                    alert("Study created successfully!");
                }
                else {
                    alert("Study creation failed!");
                }
            })
    };



    useEffect(() => {
        for(const element of mooclets) {
            element.parameters = assignerHandleVersionOrVariableDeletion(element.policy, element.parameters, versions, variables);
        }
        sMooclets(mooclets);
    }, [variables, versions]) //TO Improve: how to do it only when variables or versions deletion?

    useEffect(() => {
        handleOpen(1);
        // TODO: Think about how to open all the mooclets from cookies.
        if(theStudy['_id']['$oid'] == 1998) {
            // TODO: Now we just make them start from empty. But in the future we should allow people to make progress on unfinished study set up!
            sStatus(1);
        }
        else {
            fetch(`/apis/load_existing_study?deployment=${deploymentName}&study=${theStudy['name']}`)
            .then(response => response.json())
            .then(data => {

                let mooclets = JSON.parse(JSON.stringify(data['mooclets']));
                let o = mooclets[0]['parameters']['regressionFormulaItems']
                let oM = [];
                for(const element of o) {
                    oM.push(element)
                }
                console.log(o)
                console.log(oM)
                sStudyName(data['studyName']);
                sVariables(data['variables']);
                sVersions(data['versions']);
                sMooclets(mooclets);
                sFactors(data['factors']);
                sRewardInformation(data['rewardInformation']);
                sStatus(2);
            })
            .catch((error) => {
                console.error('Error:', error);
            })
        }
    }, [theStudy]);

    const handleModifyStudy = () => {
        fetch('/apis/modify_existing_study', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deployment": deploymentName, // TODO: change to "deploymentId
                "study": studyName,
                "mooclets": mooclets,
                "variables": variables,
                "factors": factors,
                "versions": versions, 
                "rewardInformation": rewardInformation
            })
        })
            .then(response => response.json())
            .then(data => {
                alert("Study created successfully!");
            })
    };
    
    const getWeight = (node) => {
        // get all slibings.
        let siblings = mooclets.filter(mooclet => mooclet.parent === node.parent);
        // get total weights of siblings.
        let totalWeight = 0;
        for(const element of siblings) {
            totalWeight += parseInt(element.weight);
        }

        return Math.round(node.weight/totalWeight * 10000 / 100) + "%";
    }
    return (
        <Container sx={{mt: 4}}>
            <Box>
                {status === 1 && <TextField sx={{ mb: 3 }} label="Study name" value={studyName} onChange={(e) => sStudyName(e.target.value)}></TextField>}


                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="reward-editor"
                    >
                        <Typography variant='h6'>Reward</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <RewardEditor rewardInformation={rewardInformation} sRewardInformation={sRewardInformation} />
                    </AccordionDetails>
                </Accordion>
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
                        <Typography variant='h6'>Factors & Versions</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <VersionFactorsEditor allowVersionNameChange={status === 1} factors={factors} sFactors={sFactors} versions={versions} sVersions={sVersions}/>


                        <VersionEditor allowVersionNameChange={status === 1} factors = {factors} versions={versions} sVersions={sVersions} />
                    </AccordionDetails>
                </Accordion>
                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="mooclet-graph"
                        id="mooclet-graph"
                    >
                        <Typography variant='h6'>Designer Graph</Typography>
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
                                        <Input className="assigner-weight-input" type="number" variant="standard" value = {node.weight} onChange={(event) => handleMOOCletWeightChange(event, node.id)} />
                                        <small>{getWeight(node)}</small>
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



                {studyName !== "" && <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="study-api-doc"
                        id="study-api-doc"
                    >
                        <Typography variant='h6'>APIs for {studyName} in {deploymentName}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <APICard studyName={studyName} deploymentName={deploymentName}></APICard>
                    </AccordionDetails>
                </Accordion>}

                {status === 1 && <Button sx={{ mt: 2 }} variant="contained" onClick={handleCreateStudy} fullWidth>Create this study.</Button>}
                {status === 2 && <Button sx={{ mt: 2 }} variant="contained" onClick={handleModifyStudy} fullWidth>Modify this study.</Button>}
            </Box>
            <Modal
                open={moocletModalOpen}
                onClose={handleMOOCletModalClose}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <MOOCletEditor mooclets={mooclets} sMooclets={sMooclets} idToEdit={idToEdit} variables={variables} factors={factors}></MOOCletEditor>
                </Box>
            </Modal>
        </Container>
    );
}


export default StudyEditor;