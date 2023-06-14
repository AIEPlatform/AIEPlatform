import { React, useState } from 'react';
import { TextField} from '@mui/material';

function MoocletNameEditor(props) {
    let moocletName = props.moocletName;
    let sMoocletName = props.sMoocletName;


    return (
        <TextField
            id="mooclet-name-input"
            label="Mooclet name"
            onChange={(e) => sMoocletName(e.target.value)}
            width = "100%"
        />
    )
}


export default MoocletNameEditor;