import React, { useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box } from '@mui/material';
import CommonAssignerAttribute from '../../CommonAssignerAttributes';


export function versionChangeHandler() {

}

export function variableChangeHandler() {
}

export const name = "Uniform Random";

export function main(props) {
    // return hello world.
    return (
        <Box>
            <CommonAssignerAttribute
                assigners={props.assigners}
                myId={props.myId}
                sAssigners={props.sAssigners}
            />
        </Box>
    );
}