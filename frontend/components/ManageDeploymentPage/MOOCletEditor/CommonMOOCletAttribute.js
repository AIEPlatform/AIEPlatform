import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem, Checkbox, FormControlLabel } from '@mui/material';
import Select from 'react-select';


function CommonMOOCletAttribute(props) {
    let mooclets = props.mooclets;
    let sMooclets = props.sMooclets;
    let myId = props.myId;
    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);


    return (
        <Box>
            <FormControlLabel
                control={<Checkbox checked={mooclet['isConsistent'] || false} onChange={(e) => {
                    mooclet['isConsistent'] = e.target.checked;
                    sMooclets(tree)
                }} />}
                label="Consistent assignment"
            />
            <FormControlLabel
                control={<Checkbox checked={mooclet['reassignBeforeReward'] || false} onChange={(e) => {
                    mooclet['reassignBeforeReward'] = e.target.checked;
                    sMooclets(tree)
                }} />}
                label="Allow to re-assign treatment before a reward is received."
            />
        </Box>
    )
}


export default CommonMOOCletAttribute;