import { React } from 'react';
import { TextField, Box, Checkbox, FormControlLabel } from '@mui/material';

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
                }} />}
                label="Re-assign a treatment only if the previous one has received a reward"
            />

            <TextField
                sx={{ m: 1 }}
                required
                label={`Auto Zero Threshold (in seconds)`}
                type="number"
                value={assigner['autoZeroThreshold'] || ""}
                onChange={(e) => {
                    assigner['autoZeroThreshold'] = parseFloat(e.target.value);
                    sAssigners(tree);
                }}
            />
        </Box>
    )
}


export default CommonAssignerAttribute;