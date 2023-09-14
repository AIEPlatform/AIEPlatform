import React, { useState } from 'react';
import dynamic from 'next/dynamic'
const QuillNoSSRWrapper = dynamic(import('react-quill'), {	
	ssr: false,
	loading: () => <p>Loading ...</p>,
	})

function AdvancedVersionEditor(props) {

    const handleVersionContentChange = (current) => {
        let index = props.tinyMCEEditorIndex;
        let data = {...props.study};
        data['versions'][index]['content'] = current;
        props.sStudy(data);
    }

  return <QuillNoSSRWrapper  theme="snow" value={props.study['versions'][props.tinyMCEEditorIndex]['content']} onChange={(current) => {handleVersionContentChange(current)}} />
}


export default AdvancedVersionEditor;