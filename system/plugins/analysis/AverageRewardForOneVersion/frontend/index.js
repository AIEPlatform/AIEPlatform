// load useEffect
import React, { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import { Stack, Typography, IconButton } from '@mui/material';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ErrorBar } from 'recharts';

// Loading average reward by time dataframe.

const distinctColors = ["red", "blue", "green", "orange", "purple", "pink", "cyan", "magenta", "teal"];

export const name = "Average Reward By Time For One Version (Not Complete Yet)"

export function main(props) {
  const theDataset = props.theDataset;
  const analysis = props.analysis;
  const closeButtonClickHandler = props.closeButtonClickHandler;
  const [resultDf, sResultDf] = useState([]);
  const [groups, sGroups] = useState([]);
  useEffect(() => {
    if (theDataset == null) return;
    fetch('/apis/analysis/analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        theDatasetId: theDataset['_id']['$oid']
      })
    })
      .then(res => res.json())
      .then(data => {
        sResultDf(data['result']['data']);
        sGroups(data['result']['groups']);
      })
      .catch(err => console.log(err))
  }, [theDataset,props.datasetTime])

  return (
    <>
    <Container style={{ maxHeight: "100%", display: 'flex', flexDirection: 'column' }}>
      <Stack direction="row" justifyContent="space-between">
        <Typography variant='h6'>Average Reward as a function of time</Typography>
        <IconButton onClick={() => closeButtonClickHandler(analysis)}>
          <CloseOutlinedIcon />
        </IconButton>
      </Stack>
    </Container>

    <div style={{ maxWidth: '100%', maxHeight: '500px' }}>
      <ResponsiveContainer width="100%" height="100%" aspect={2}>
          <LineChart
            width={500}
            height={300}
            data={resultDf}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" />
            <YAxis label={{ value: "Reward", position: "insideLeft", angle: -90}}/>
            <ErrorBar dataKey="errorY" width={4} strokeWidth={2} stroke="green" direction="y" />
            <Tooltip />
            <Legend />
            {
              groups.map((group, index) => {
                return <Line key = {index} type="monotone" dataKey={group} stroke={distinctColors[index % 9]} activeDot={{ r: 8 }} />
              })
            }
          </LineChart>
      </ResponsiveContainer>
    </div>
    </>
  );
}
