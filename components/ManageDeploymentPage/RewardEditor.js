import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';

function RewardEditor(props) {
    let rewardInformation = props.rewardInformation;
    let sRewardInformation = props.sRewardInformation;


    return (
        <Paper sx={{
            m:1, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            <TextField
                required
                sx={{ mt: 1 }}
                id="new-variable-name-input"
                label="Reward Name"
                value={rewardInformation['name']}
                onChange={(e) => {
                    let newRewardInformation = {...rewardInformation};
                    newRewardInformation['name'] = e.target.value;
                    sRewardInformation(newRewardInformation);
                }}
                width="100%"
            />

            <TextField
                sx={{ mt: 1 }}
                id="outlined-number"
                label="Min Value"
                type="number"
                value={rewardInformation['min']}
                onChange={(e) => {
                    let newRewardInformation = {...rewardInformation};
                    newRewardInformation['min'] = e.target.value;
                    sRewardInformation(newRewardInformation);
                }}
            />

            <TextField
                sx={{ mt: 1, mb: 1 }}
                id="outlined-number"
                label="Max Value"
                type="number"
                value={rewardInformation['max']}
                onChange={(e) => {
                    let newRewardInformation = {...rewardInformation};
                    newRewardInformation['max'] = e.target.value;
                    sRewardInformation(newRewardInformation);
                }}
            />
        </Paper>
    )
}


export default RewardEditor;