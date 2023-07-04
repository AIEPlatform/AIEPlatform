import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';
import CommonMOOCletAttribute from './CommonMOOCletAttribute';

function UniformRandom(props) {
    let versions = props.versions;
    let mooclets = props.mooclets;
    let myId = props.myId;
    let sMooclets = props.sMooclets;
    let tree = [...mooclets];
    let mooclet = tree.find(mooclet => mooclet.id === myId);


    let handleWeightChange = (index, event) => {
        let data = [...mooclets];
        let mooclet = data.find(mooclet => mooclet.id === myId);
        mooclet['parameters'][versions[index]['name']] = Number(event.target.value);
        sMooclets(data);
    }
    return (
        <Box>
            <CommonMOOCletAttribute
                mooclets={mooclets}
                myId={myId}
                sMooclets={sMooclets}
            />
        </Box>
    )
}


export default UniformRandom;