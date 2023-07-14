import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';
import CommonAssignerAttribute from './CommonAssignerAttribute';

function UniformRandom(props) {
    let assigners = props.assigners;
    let myId = props.myId;
    let sAssigners = props.sAssigners;
    let tree = [...assigners];
    return (
        <Box>
            <CommonAssignerAttribute
                assigners={assigners}
                myId={myId}
                sAssigners={sAssigners}
            />
        </Box>
    )
}


export default UniformRandom;