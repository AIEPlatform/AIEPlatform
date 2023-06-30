// load useEffect
import React, { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import Typography  from '@mui/material/Typography';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ErrorBar } from 'recharts';

// Loading average reward by time dataframe.

const distinctColors = ["red", "blue", "green", "orange", "purple", "pink", "cyan", "magenta", "teal"];

export default function AverageRewardByTimeForOneVersion(props) {
  const theDataset = props.theDataset;
  const [resultDf, sResultDf] = useState([]);
  const [groups, sGroups] = useState([]);
  useEffect(() => {
    if (theDataset == null) return;
    fetch('/apis/analysis/AverageRewardByTime', {
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
        sResultDf(data['data']);
        sGroups(data['groups']);
      })
      .catch(err => console.log(err))
  }, [theDataset,props.datasetTime])

  return (
    <>
    <Container style={{ maxHeight: "100%", display: 'flex', flexDirection: 'column' }}>
    <Typography variant='h6'>Average Reward as a function of time</Typography>
    </Container>
    <ResponsiveContainer>
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
    </>
  );
}
