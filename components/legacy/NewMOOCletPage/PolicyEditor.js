import { React, useState } from 'react';
import { Typography, Paper, TextField, Bo, Button, Box, MenuItem, Divider } from '@mui/material'
import OnePolicyEditor from './OnePolicyEditor';

function PolicyEditor(props) {
    let policies = props.policies;
    let sPolicies = props.sPolicies;
    let versions = props.versions;
    let variables = props.variables;

    const addFields = () => {
        let newfield = { type: '', parameter: '' }
        sPolicies([...policies, newfield])
    }


    return (
        <Paper sx={{
            m: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column'
        }}>
            {policies.map((input, index) => {
                return (
                    <Box key = {index}>
                    <OnePolicyEditor policyIndex = {index} versions = {versions} variables = {variables} key = {index} input = {input} index = {index} sPolicies = {sPolicies} policies = {policies}></OnePolicyEditor>
                    {index!== (policies.length - 1) && <Divider></Divider>}
                    </Box>
                )
            })}

            <Button onClick = {(e) => addFields()} variant="contained" color="primary" sx = {{m: 1}}>Add More Policy</Button>
        </Paper>
    )
}


export default PolicyEditor;