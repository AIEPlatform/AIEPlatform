import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';


function CommonAssignerAttribute(props) {
    let assigners = props.assigners;
    let sAssigners = props.sAssigners;
    let myId = props.myId;
    let tree = [...assigners];
    let assigner = tree.find(assigner => assigner.id === myId);


    return (
        <Box>
            <FormControlLabel
                control={<Checkbox checked={assigner['isConsistent'] || false} onChange={(e) => {
                    assigner['isConsistent'] = e.target.checked;
                    sAssigners(tree)
                }} />}
                label="Consistent assignment"
            />
            <FormControlLabel
                control={<Checkbox checked={assigner['reassignAfterReward'] || false} onChange={(e) => {
                    assigner['reassignAfterReward'] = e.target.checked;
                    sAssigners(tree)
                    console.log(tree);
                }} />}
                label="Re-assign a treatment only if the previous one has received a reward"
            />
        </Box>
    )
}


export default CommonAssignerAttribute;