import { React, useState, useRef, useEffect } from 'react';
import { Typography, TextField, Box, Button, Container, Input, Checkbox, FormControl, FormGroup, FormControlLabel, Tabs, Tab } from '@mui/material';
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
import AssignerEditor from './AssignerEditor/AssignerEditor';
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

    let [tabIndex, sTabIndex] = useState(0);

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
            "weight": 1
        }
    ];

    const newStudy = {
        "name": "",
        "variables": [],
        "factors": [],
        "versions": [],
        "assigners": designGraph,
        "rewardInformation": {
            "name": "reward",
            "min": 0,
            "max": 1
        },
        "simulationSetting": {
            "baseReward": {},
            "contextualEffects": [],
            "numDays": 5
        },
        "status": "stopped"
    }
    const [study, sStudy] = useState(
        newStudy
    );


    const [status, sStatus] = useState(0); // 0: loading, 1: new study, 2: existing study., 4: loading exiting study
    const deploymentName = props.deploymentName;
    const handleDrop = (newTreeData) => {
        // check if two nodes have parent as 0. If so, alert user that they can't do that.
        let rootNodes = newTreeData.filter(node => node.parent === 0);
        if (rootNodes.length > 1) {
            alert("You cannot have more than one root node!");
            return;
        }
        sAssigners(newTreeData)
    };
    const [assignerModalOpen, sAssignerModalOpen] = useState(false);
    const [idToEdit, sIdToEdit] = useState(null);
    const treeRef = useRef(null);
    const handleOpen = (nodeId) => treeRef.current.open(nodeId);

    const addAssigner = () => {
        let newId = study.assigners.length + 1;
        let newAssigner = {
            "id": newId,
            "parent": 1,
            "droppable": true,
            "isOpen": true,
            "text": `assigner${newId}`,
            "name": `assigner${newId}`,
            "policy": "UniformRandom",
            "parameters": {},
            "weight": 1
        }
        sAssigners([...study.assigners, newAssigner]);

        handleOpen(newId);
    };

    const handleAssignerModalClose = () => {
        sAssignerModalOpen(false);
        sIdToEdit(null);
    };

    const handleAssignerWeightChange = (event, myId) => {
        let data = [...study.assigners];
        let assigner = data.find(assigner => assigner.id === myId);
        assigner['weight'] = event.target.value;
        sAssigners(data);
    }

    const handleAssignerRemove = (myId) => {
        // check if this is the root node (if it is, alert user they can't remove the root one)
        if (myId === 1) {
            alert("You cannot remove the root assigner!");
            return;
        }
        let Tree = [...study.assigners];
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

        sAssigners(Tree);

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
    }, [study.variables.length, study.versions.length, study.factors.length]); // also listen on the array of parameters of all assigners

    useEffect(() => {
        handleOpen(1);
        // TODO: Think about how to open all the assigners from cookies.
        if (theStudy['_id']['$oid'] != 1998) {
            loadCurrentStudy();
        }
        else {
            sStatus(1);
            sStudy(newStudy);
        }
    }, [theStudy]);

    const handleModifyStudy = () => {
        // validate the study
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
                if (data["status_code"] === 200) alert("Study modified successfully!");
                else alert(data["message"])
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
        let siblings = study.assigners.filter(assigner => assigner.parent === node.parent);
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
        sStudy(temp);
    }

    const sVariables = setStudyAttributes.bind('variables');
    const sVersions = setStudyAttributes.bind('versions');
    const sFactors = setStudyAttributes.bind('factors');
    const sStudyName = setStudyAttributes.bind('name');
    const sRewardInformation = setStudyAttributes.bind('rewardInformation');
    const sAssigners = setStudyAttributes.bind('assigners');
    const sSimulationSetting = setStudyAttributes.bind('simulationSetting');



    return (
        <Container>
            <Box>
                <Box sx={{ mb: 2 }}>
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" onClick={handleModifyStudy} startIcon={<EditIcon />}>Modify</Button>}
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={handleResetStudy} startIcon={<RestartAltIcon />}>Reset</Button>}
                    {status === 2 && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={handleDeleteStudy} startIcon={<DeleteIcon />}>Delete</Button>}
                    <Box>
                        <FormGroup>
                            <FormControlLabel control={<Checkbox checked={study['status'] === 'running'} onChange={
                                (e) => {

                                    let temp = { ...study };
                                    temp['status'] = e.target.checked ? 'running' : 'stopped';
                                    sStudy(temp);
                                }
                            } />} label="Start the study" />
                        </FormGroup>
                    </Box>
                </Box>

                {status === 2 && <Container sx={{ mb: 2 }}>
                    <Tabs value={tabIndex} onChange={(e, newValue) => { sTabIndex(newValue) }} aria-label="basic tabs example">
                        <Tab label="Configuration" />
                        <Tab label="Simulations" />
                    </Tabs>
                </Container>}

                {tabIndex === 0 && <Box sx={{ mb: 2 }}>
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
                            aria-controls="assigner-graph"
                            id="assigner-graph"
                        >
                            <Typography variant='h6' sx={{ display: 'flex', alignItems: 'center' }}><ArrowForwardIcon sx={{ mr: 1 }}></ArrowForwardIcon>Assigner Graph</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <DndProvider backend={MultiBackend} options={getBackendOptions()}>
                                {/* https://www.npmjs.com/package/@minoru/react-dnd-treeview */}
                                <Tree
                                    ref={treeRef}
                                    tree={study.assigners}
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
                                            <Input className="assigner-weight-input" type="number" variant="standard" value={node.weight} onChange={(event) => handleAssignerWeightChange(event, node.id)} />
                                            <small>{getWeight(node)}</small>
                                            <Button onClick={() => {
                                                sIdToEdit(node.id);
                                                sAssignerModalOpen(true);
                                            }} startIcon={<EditIcon />}>Edit</Button>


                                            <Button onClick={() => handleAssignerRemove(node.id)} startIcon={<CloseIcon />} color='error'>Delete</Button>
                                        </Box>
                                    )}
                                />
                            </DndProvider>
                            <Button sx={{ m: 2 }} variant="contained" onClick={addAssigner}>Add a new Assigner</Button>
                        </AccordionDetails>
                    </Accordion>
                </Box>}



                {tabIndex === 1 &&
                    <SimulationEditor studyName={study.name} deploymentName={deploymentName} versions={study.versions} variables={study.variables} simulationSetting={study.simulationSetting} sSimulationSetting={sSimulationSetting} />
                }
            </Box>
            <Box sx={{ mb: 2 }}>
                {status === 1 && <Button sx={{ m: 1 }} variant="outlined" onClick={handleCreateStudy} startIcon={<AddCircleIcon />} fullWidth>Create</Button>}
            </Box>
            <Modal
                open={assignerModalOpen}
                onClose={handleAssignerModalClose}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <AssignerEditor assigners={study.assigners} sAssigners={sAssigners} idToEdit={idToEdit} variables={study.variables} factors={study.factors} versions={study.versions}></AssignerEditor>
                </Box>
            </Modal>
        </Container >
    );
}


export default StudyEditor;