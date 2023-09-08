import { React, useEffect, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, useForkRef } from '@mui/material';
import CommonAssignerAttribute from '../../CommonAssignerAttributes';


export function versionChangeHandler() {

}

export function variableChangeHandler() {
}

export const name = "GPT(notFinished!)";

export function main(props) {
    let assigners = props.assigners;
    let myId = props.myId;
    let sAssigners = props.sAssigners;
    let tree = [...assigners];
    let assigner = tree.find(assigner => assigner.id === myId);

    // Initial policy parameter
    useEffect(() => {
        if (!assigner['parameters']['prompt']) {
            assigner['parameters']['prompt'] = '';
        }
        if (!assigner['parameters']['initialPrompt']) {
            assigner['parameters']['initialPrompt'] = '';
        }
        sAssigners(tree);
    }, []);
    return (
        <Box>
            <Typography variant="h6">Initial Prompt</Typography>
            <TextField
                id="outlined-multiline-static"
                label="Initial Prompt"
                multiline
                rows={4}
                fullWidth={true}
                defaultValue={assigner['parameters']['initialPrompt']}
                onChange={(e) => {
                    assigner['parameters']['initialPrompt'] = e.target.value;
                    sAssigners(tree);
                }}
            />

            <Typography variant="h6">Prompt</Typography>
            <TextField
                id="outlined-multiline-static"
                label="Prompt"
                multiline
                rows={4}
                fullWidth={true}
                defaultValue={assigner['parameters']['prompt']}
                onChange={(e) => {
                    assigner['parameters']['prompt'] = e.target.value;
                    sAssigners(tree);
                }}
            />
        </Box>
    )
}