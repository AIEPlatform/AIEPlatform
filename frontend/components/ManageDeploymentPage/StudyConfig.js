import { React, useState, useRef, useEffect } from 'react';
import { Typography, Box, Button, Input } from '@mui/material';
import VariableEditor from '../ManageDeploymentPage/VariableEditor';
import FactorsEditor from './FactorsEditor';
import VersionEditor from './VersionEditor';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import RewardEditor from './RewardEditor';
import validifyStudy from '../../helpers/validifyStudy';
import ScaleIcon from '@mui/icons-material/Scale';
import AttributionIcon from '@mui/icons-material/Attribution';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AbcIcon from '@mui/icons-material/Abc';
import {
    Tree,
    getBackendOptions,
    MultiBackend,
} from "@minoru/react-dnd-treeview";
import { DndProvider } from "react-dnd";

function StudyConfig(props) {

    let study = props.study;
    let sStudy = props.sStudy;
    let sIdToEdit = props.sIdToEdit;

    let existingVariables = props.existingVariables;
    let sExistingVariables = props.sExistingVariables;

    let setStudyAttributes = props.setStudyAttributes;
    let sAssignerModalOpen = props.sAssignerModalOpen;

    const treeRef = useRef(null);
    let handleOpen = (nodeId) => treeRef.current.open(nodeId);

    useEffect(() => {
        if (study === null) return;
        handleOpen(1);
    }, [study]);


    useEffect(() => {
        if (study === null) return;
        let modifiedStudy = validifyStudy(study, existingVariables);
        sStudy(modifiedStudy);
    }, [study?.variables.length, study?.versions.length, study?.factors.length, existingVariables]); // also listen on the array of parameters of all assigners

    const handleDrop = (newTreeData) => {
        // check if two nodes have parent as 0. If so, alert user that they can't do that.
        let rootNodes = newTreeData.filter(node => node.parent === 0);
        if (rootNodes.length > 1) {
            alert("You cannot have more than one root node!");
            return;
        }
        sAssigners(newTreeData)
    };

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


    // Need to use with bind.

    const sVariables = setStudyAttributes.bind('variables');
    const sVersions = setStudyAttributes.bind('versions');
    const sFactors = setStudyAttributes.bind('factors');
    const sRewardInformation = setStudyAttributes.bind('rewardInformation');
    const sAssigners = setStudyAttributes.bind('assigners');


    const autoGenerateVersionJSON = () => {
        // Check if any two versions have the same name.
        // If so, return and alert.
        // Every version has version['name'].


        let data = [...study.versions];
        let allFactors = [];
        // for factors are version names;
        for (let i = 0; i < data.length; i++) {
            let factor = data[i]['name'];
            allFactors.push(factor);
        }

        // get unique factors
        let uniqueFactors = [...new Set(allFactors)];
        if(uniqueFactors.length !== allFactors.length){
            alert("Version names must be unique!");
            return;
        }

        // for each version, the versionJSON is all factors, with its version name to be 1.

        for (let i = 0; i < data.length; i++) {
            let versionJSON = {};
            for (let j = 0; j < uniqueFactors.length; j++) {
                let factor = uniqueFactors[j];
                if (factor === data[i]['name']) {
                    versionJSON[factor] = 1;
                } else {
                    versionJSON[factor] = 0;
                }
            }
            data[i]['versionJSON'] = versionJSON;
        }

        console.log(data)

        sVersions(data);
        sFactors(uniqueFactors);
    }

    if (study === null) return (<div></div>);
    return (
        <Box sx={{ mb: 2 }}>
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
                    <VariableEditor sExistingVariables={sExistingVariables} existingVariables={existingVariables} selectedVariables={study.variables} sSelectedVariables={sVariables} />
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
                    <Button onClick={(e) => autoGenerateVersionJSON()} variant="contained" color="primary" sx={{ m: 1 }}>!DANGER: WE DON'T KNOW HOW IT WILL AFFECT ON-GOING ASSIGNERS. DO IT WITH YOUR OWN RISK. Automatically generate version JSON</Button>
                    <FactorsEditor allowVersionNameChange={study['status'] === "reset"} factors={study.factors} sFactors={sFactors} versions={study.versions} sVersions={sVersions} />
                    <VersionEditor allowVersionNameChange={study['status'] === "reset"} factors={study.factors} versions={study.versions} sVersions={sVersions} />
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
        </Box>
    );
}


export default StudyConfig;