import { React, useState, useRef, useEffect } from 'react';
import { Typography, TextField, Box, Button, Container, Input } from '@mui/material';
import VariableEditor from '../ManageDeploymentPage/VariableEditor';
import FactorsEditor from './FactorsEditor';
import VersionEditor from './VersionEditor';
import SimulationEditor from './SimulationEditor';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import Modal from '@mui/material/Modal';
import MOOCletEditor from './MOOCletEditor/MOOCletEditor';
import RewardEditor from './RewardEditor';
import validifyStudy from '../../helpers/validifyStudy';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import ScaleIcon from '@mui/icons-material/Scale';
import AttributionIcon from '@mui/icons-material/Attribution';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AutoModeIcon from '@mui/icons-material/AutoMode';
import AbcIcon from '@mui/icons-material/Abc';

import {
    Tree,
    getBackendOptions,
    MultiBackend,
} from "@minoru/react-dnd-treeview";
import { DndProvider } from "react-dnd";

function StudyEditor(props) {

    let theStudy = props.theStudy; // theStudy is not study!
    let sTheStudies = props.sTheStudies;
    let sTheStudy = props.sTheStudy;

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
    ];

    const newStudy = {
        "name": "",
        "variables": [],
        "factors": [],
        "versions": [],
        "mooclets": designGraph,
        "rewardInformation": {
            "name": "reward",
            "min": 0,
            "max": 1
        },
        "simulationSetting": {
            "baseReward": {},
            "contextualEffects": [],
            "numDays": 5
        }
    }
    const [study, sStudy] = useState(
        newStudy
    );


    const [status, sStatus] = useState(0); // 0: loading, 1: new study, 2: existing study., 4: loading exiting study
    const deploymentName = props.deploymentName;
    const handleDrop = (newTreeData) => sMooclets(newTreeData);
    const [moocletModalOpen, sMoocletModalOpen] = useState(false);
    const [idToEdit, sIdToEdit] = useState(null);
    const treeRef = useRef(null);
    const handleOpen = (nodeId) => treeRef.current.open(nodeId);

    const addMOOClet = () => {
        let newId = study.mooclets.length + 1;
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
        sMooclets([...study.mooclets, newMOOClet]);

        handleOpen(newId);
    };

    const handleMOOCletModalClose = () => {
        sMoocletModalOpen(false);
        sIdToEdit(null);
    };

    const handleMOOCletWeightChange = (event, myId) => {
        let data = [...study.mooclets];
        let mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['weight'] = event.target.value;
        sMooclets(data);
    }

    const handleMOOCletRemove = (myId) => {
        let Tree = [...study.mooclets];
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
        fetch('/apis/experimentDesign/study', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deploymentName": deploymentName, // TODO: change to "deploymentId
                "study": study
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] == 200) {
                    alert("Study created successfully!");
                    sTheStudies([theStudy].concat(data["studies"]));
                    sTheStudy(data['study']);

                }
                else {
                    alert(data['message']);
                }
            })
    };

    const loadCurrentStudy = () => {
        fetch(`/apis/experimentDesign/study?deployment=${deploymentName}&study=${theStudy['name']}`)
            .then(response => response.json())
            .then(data => {
                sStatus(4);
                sStudy(data['study']);
                sStatus(2);
            })
            .catch((error) => {
                console.error('Error:', error);
            })
    }


    // Call the helper function to validate the study.
    useEffect(() => {
        let modifiedStudy = validifyStudy(study);
        sStudy(modifiedStudy);
    }, [study.variables.length, study.versions.length, study.factors.length]);

    useEffect(() => {
        handleOpen(1);
        // TODO: Think about how to open all the mooclets from cookies.
        if (theStudy['_id']['$oid'] != 1998) {
            loadCurrentStudy();
        }
        else {
            sStatus(1);
            sStudy(newStudy);
        }
    }, [theStudy]);

    const handleModifyStudy = () => {
        fetch('/apis/experimentDesign/study', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deployment": deploymentName, // TODO: change to "deploymentId
                "study": study
            })
        })
            .then(response => response.json())
            .then(data => {
                alert("Study modified successfully!");
            })
            .catch((error) => {
                alert("Study modification failed!")
            })
    };

    const handleResetStudy = () => {
        if (!confirm("Are you sure you want to reset the study? The study will be reverted to earliest status after last reset. The interactions/datasets associated will all be deleted.")) return;
        fetch('/apis/experimentDesign/resetStudy', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deployment": deploymentName, // TODO: change to "deploymentId
                "study": study['name']
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    loadCurrentStudy();
                    alert("reset successfully!")
                }
                else {
                    alert("Something is wrong.");
                }
            }).catch((error) => {
                alert("Something is wrong.");
            })
    }

    const getWeight = (node) => {
        // get all slibings.
        let siblings = study.mooclets.filter(mooclet => mooclet.parent === node.parent);
        // get total weights of siblings.
        let totalWeight = 0;
        for (const element of siblings) {
            totalWeight += parseInt(element.weight);
        }

        return Math.round(node.weight / totalWeight * 10000 / 100) + "%";
    };


    const handleDeleteStudy = () => {
        if (!confirm("Are you sure you want to delete the study? Everything associated to this study will be erased. This operation is NON-UNDOABLE.")) return;
        fetch('/apis/experimentDesign/study', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deployment": deploymentName, // TODO: change to "deploymentId
                "study": study.name
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    alert("Study deleted successfully!");
                    sStatus(1);
                    location.reload();
                }
                else {
                    alert("Study deletion failed!");
                }
            })
    };

    // Need to use with bind.
    const setStudyAttributes = function (newAttribute) {
        let temp = { ...study };
        temp[this] = newAttribute;
        console.log(this)
        console.log(newAttribute)
        console.log(temp)
        sStudy(temp);
    }

    const sVariables = setStudyAttributes.bind('variables');
    const sVersions = setStudyAttributes.bind('versions');
    const sFactors = setStudyAttributes.bind('factors');
    const sStudyName = setStudyAttributes.bind('name');
    const sRewardInformation = setStudyAttributes.bind('rewardInformation');
    const sMooclets = setStudyAttributes.bind('mooclets');
    const sSimulationSetting = setStudyAttributes.bind('simulationSetting');



    return (
        <Container>
            <Box>
                <Box sx={{ mb: 2 }}>
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" onClick={handleModifyStudy} startIcon={<EditIcon />}>Modify</Button>}
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={handleResetStudy} startIcon={<RestartAltIcon />}>Reset</Button>}
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={handleDeleteStudy} startIcon={<DeleteIcon />}>Delete</Button>}
                </Box>

                {status === 1 && <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="name-editor"
                    >
                        <Typography variant='h6'>Study name</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <TextField required sx={{ mb: 3 }} label="Study name" value={study.name} onChange={(e) => sStudyName(e.target.value)}></TextField>
                    </AccordionDetails>
                </Accordion>}


                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="reward-editor"
                    >
                        <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><ScaleIcon sx={{ mr: 1 }}></ScaleIcon>Reward</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <RewardEditor rewardInformation={study.rewardInformation} sRewardInformation={sRewardInformation} />
                    </AccordionDetails>
                </Accordion>
                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                    >
                        <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><AttributionIcon sx={{ mr: 1 }}></AttributionIcon>Variables</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <VariableEditor selectedVariables={study.variables} sSelectedVariables={sVariables} />
                    </AccordionDetails>
                </Accordion>

                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1a-content"
                        id="panel1a-header"
                    >
                        <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><AbcIcon sx={{ mr: 1 }}></AbcIcon>Factors & Versions</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <FactorsEditor allowVersionNameChange={status === 1} factors={study.factors} sFactors={sFactors} versions={study.versions} sVersions={sVersions} />


                        <VersionEditor allowVersionNameChange={status === 1} factors={study.factors} versions={study.versions} sVersions={sVersions} />
                    </AccordionDetails>
                </Accordion>
                <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="mooclet-graph"
                        id="mooclet-graph"
                    >
                        <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><ArrowForwardIcon sx={{ mr: 1 }}></ArrowForwardIcon>Designer Graph</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <DndProvider backend={MultiBackend} options={getBackendOptions()}>
                            {/* https://www.npmjs.com/package/@minoru/react-dnd-treeview */}
                            <Tree
                                ref={treeRef}
                                tree={study.mooclets}
                                rootId={0}
                                onDrop={handleDrop}
                                initialOpen={true}
                                sort={false}
                                render={(node, { depth, isOpen, onToggle }) => (
                                    <Box style={{ marginLeft: depth * 10 }}>
                                        {node.droppable && (
                                            <span onClick={onToggle}>{isOpen ? "[-]" : "[+]"}</span>
                                        )}
                                        <Typography sx={{ m: 0.5 }} variant='span' component='strong'>{node.name}</Typography>
                                        <Typography sx={{ m: 0.5 }} variant='span'>Weight:</Typography>
                                        <Input className="assigner-weight-input" type="number" variant="standard" value={node.weight} onChange={(event) => handleMOOCletWeightChange(event, node.id)} />
                                        <small>{getWeight(node)}</small>
                                        <Button onClick={() => {
                                            sIdToEdit(node.id);
                                            sMoocletModalOpen(true);
                                        }} startIcon={<EditIcon />}>Edit</Button>


                                        <Button onClick={() => handleMOOCletRemove(node.id)} startIcon={<CloseIcon />} color='error'>Delete</Button>
                                    </Box>
                                )}
                            />
                        </DndProvider>
                        <Button sx={{ m: 2 }} variant="contained" onClick={addMOOClet}>Add a new Assigner</Button>
                    </AccordionDetails>
                </Accordion>


                {status === 2 && <Accordion>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="mooclet-graph"
                        id="mooclet-graph"
                    >
                        <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><AutoModeIcon sx={{ mr: 1 }}></AutoModeIcon>Simulations</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <SimulationEditor studyName={study.name} deploymentName={deploymentName} versions={study.versions} variables={study.variables} simulationSetting={study.simulationSetting} sSimulationSetting={sSimulationSetting} />
                    </AccordionDetails>
                </Accordion>
                }
            </Box>

            <Box sx={{ mb: 2 }}>
                {status === 1 && <Button sx={{ m: 1 }} variant="outlined" onClick={handleCreateStudy} startIcon={<AddCircleIcon />} fullWidth>Create</Button>}
            </Box>
            <Modal
                open={moocletModalOpen}
                onClose={handleMOOCletModalClose}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <MOOCletEditor mooclets={study.mooclets} sMooclets={sMooclets} idToEdit={idToEdit} variables={study.variables} factors={study.factors} versions={study.versions}></MOOCletEditor>
                </Box>
            </Modal>
        </Container>
    );
}


export default StudyEditor;