import { React, useState, useRef, useEffect } from 'react';
import { Box, Button, Container, Tabs, Tab } from '@mui/material';
import StudyConfig from './StudyConfig';
import SimulationEditor from './SimulationEditor';
import EditIcon from '@mui/icons-material/Edit';
import Modal from '@mui/material/Modal';
import AssignerEditor from './AssignerEditor/AssignerEditor';
import DeleteIcon from '@mui/icons-material/Delete';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import StopIcon from '@mui/icons-material/Stop';
import StartIcon from '@mui/icons-material/Start';
import validifyStudy from '../../helpers/validifyStudy';

import AdvancedVersionEditor from './AdvancedVerionEditor';


const components = {};
let availablePolicies = [];

const context = require.context('../../plugins/policies', true, /\/frontend\/index\.js$/);
context.keys().forEach((key) => {
    const subfolderName = key.split('/')[1];
    const componentModule = context(key);

    // Assuming your components are exported as 'default'
    components[subfolderName] = componentModule;
    availablePolicies.push({
        value: subfolderName,
        label: componentModule.name
    })
});

function StudyEditor(props) {

    const [study, sStudy] = useState(null);
    let theStudy = props.theStudy; // theStudy is not study!

    const [assignerModalOpen, sAssignerModalOpen] = useState(false);
    const [idToEdit, sIdToEdit] = useState(null);

    let [existingVariables, sExistingVariables] = useState([]);

    useEffect(() => {
        fetch(`/apis/variables`)
            .then(res => res.json())
            .then(response => {
                if (response['status_code'] === 200)
                    sExistingVariables(response.data)
            })
            .catch(error => {
                alert("something is wrong with loading existing variables. Please try again later.");
            })
    }, []);

    // Call the helper function to validate the study.
    useEffect(() => {
        // TODO: Think about how to open all the assigners from cookies.
        loadCurrentStudy();
    }, [theStudy]);

    useEffect(() => {
        if (study === null) return;
        let modifiedStudy = validifyStudy(study, existingVariables, components);
        sStudy(modifiedStudy);
    }, [study?.variables.length, study?.versions.length, study?.factors.length, existingVariables]); // also listen on the array of parameters of all assigners


    let [tabIndex, sTabIndex] = useState(0);

    const deploymentName = props.deploymentName;

    const handleAssignerModalClose = () => {
        sAssignerModalOpen(false);
        sIdToEdit(null);
    };



    const loadCurrentStudy = () => {
        fetch(`/apis/experimentDesign/study?deployment=${deploymentName}&study=${theStudy['name']}`)
            .then(response => response.json())
            .then(data => {
                sStudy(data['study']);

                console.log(data['study']['simulationSetting']['contextualEffects'])
            })
            .catch((error) => {
                console.error('Error:', error);
            })
    }

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

    const handleStudyStatusChange = (newStatus) => {
        if (newStatus === "reset" && !confirm("Are you sure you want to reset the study? The study will be reverted to earliest status after last reset. The interactions/datasets associated will all be deleted.")) return;

        if (newStatus === "stopped" && !confirm("Are you sure you want to pause the study? The study will not be able to accept new rewards and it will not send treatments as well.")) return;

        if (newStatus === "running" && !confirm("Are you sure you want to start the study?")) return;
        fetch('/apis/experimentDesign/changeStudyStatus', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "deployment": deploymentName, // TODO: change to "deploymentId
                "study": study['name'],
                "status": newStatus
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data['status_code'] === 200) {
                    loadCurrentStudy();
                    if(newStatus === "running") sTabIndex(0);
                }
                else {
                    alert("Something is wrong.");
                }
            }).catch((error) => {
                alert("Something is wrong.");
            })
    }

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

    const sAssigners = setStudyAttributes.bind('assigners');
    const sSimulationSetting = setStudyAttributes.bind('simulationSetting');

    let [tinyMCEEditorIndex, setTinyMCEEditorIndex] = useState(-1);

    if (study === null) return (<div></div>);
    return (
        <Box>
            <Box>
                <Box sx={{ mb: 2 }}>
                    {study['status'] !== "running" && <Button sx={{ m: 1 }} variant="outlined" onClick={handleModifyStudy} startIcon={<EditIcon />}>Modify</Button>}
                    {study['status'] !== "running" && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={() => handleStudyStatusChange('reset')} startIcon={<RestartAltIcon />}>Reset</Button>}

                    {study['status'] === "running" && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={() => handleStudyStatusChange('stopped')} startIcon={<StopIcon />}>Pause</Button>}

                    {study['status'] !== "running" && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={() => handleStudyStatusChange('running')} startIcon={<StartIcon />}>Start</Button>}

                    {study['status'] !== "running" && <Button sx={{ m: 1 }} variant="outlined" color="error" onClick={handleDeleteStudy} startIcon={<DeleteIcon />}>Delete</Button>}
                </Box>

                {study['status'] !== "running" && <Container sx={{ mb: 2 }}>
                    <Tabs value={tabIndex} onChange={(e, newValue) => { sTabIndex(newValue) }} aria-label="basic tabs example">
                        <Tab label="Configuration" />
                        <Tab label="Simulations" />
                    </Tabs>
                </Container>}

                {tabIndex === 0 && <StudyConfig study={study} sStudy={sStudy} sIdToEdit={sIdToEdit} existingVariables = {existingVariables} sExistingVariables={sExistingVariables} setStudyAttributes = {setStudyAttributes} sAssignerModalOpen={sAssignerModalOpen} setTinyMCEEditorIndex = {setTinyMCEEditorIndex}></StudyConfig>}



                {tabIndex === 1 && 
                    <SimulationEditor study = {study} deploymentName = {deploymentName} sSimulationSetting={sSimulationSetting} />
                }
            </Box>
            <Modal
                open={assignerModalOpen}
                onClose={handleAssignerModalClose}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <AssignerEditor components = {components} availablePolicies = {availablePolicies} existingVariables = {existingVariables} study={study} assigners={study.assigners} sAssigners={sAssigners} idToEdit={idToEdit} variables={study.variables} factors={study.factors} versions={study.versions}></AssignerEditor>
                </Box>
            </Modal>


            <Modal
                open={tinyMCEEditorIndex !== -1}
                onClose={() => { setTinyMCEEditorIndex(-1) }}
                style={{ overflow: 'scroll', height: "80%", width: "80%", margin: "5% auto" }}

            >
                <Box style={{ background: "white" }}>
                    <AdvancedVersionEditor study={study} sStudy={sStudy} tinyMCEEditorIndex={tinyMCEEditorIndex} ></AdvancedVersionEditor>
                </Box>
            </Modal>
        </Box >
    );
}


export default StudyEditor;