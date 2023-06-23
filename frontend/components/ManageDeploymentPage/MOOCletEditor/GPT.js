import { React, useEffect, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, useForkRef } from '@mui/material';

function GPT(props) {
    let mooclets = props.mooclets;
    let myId = props.myId;
    let sMooclets = props.sMooclets;
    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);

    // Initial policy parameter
    useEffect(() => {
        if (!mooclet['parameters']['prompt']) {
            mooclet['parameters']['prompt'] = '';
        }
        if (!mooclet['parameters']['initialPrompt']) {
            mooclet['parameters']['initialPrompt'] = '';
        }
        sMooclets(tree);
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
                defaultValue={mooclet['parameters']['initialPrompt']}
                onChange={(e) => {
                    mooclet['parameters']['initialPrompt'] = e.target.value;
                    sMooclets(tree);
                }}
            />

            <Typography variant="h6">Prompt</Typography>
            <TextField
                id="outlined-multiline-static"
                label="Prompt"
                multiline
                rows={4}
                fullWidth={true}
                defaultValue={mooclet['parameters']['prompt']}
                onChange={(e) => {
                    mooclet['parameters']['prompt'] = e.target.value;
                    sMooclets(tree);
                }}
            />
        </Box>
    )
}


export default GPT;