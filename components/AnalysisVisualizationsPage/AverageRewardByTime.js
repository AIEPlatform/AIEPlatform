// load useEffect
import React, { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  {
    name: 'Page A',
    uv: 4000,
    pv: 2400,
    amt: 2400,
  },
  {
    name: 'Page B',
    uv: 3000,
    pv: 1398,
    amt: 2210,
  },
  {
    name: 'Page C',
    uv: 2000,
    pv: 9800,
    amt: 2290,
  },
  {
    name: 'Page D',
    uv: 2780,
    pv: 3908,
    amt: 2000,
  },
  {
    name: 'Page E',
    uv: 1890,
    pv: 4800,
    amt: 2181,
  },
  {
    name: 'Page F',
    uv: 2390,
    pv: 3800,
    amt: 2500,
  },
  {
    name: 'Page G',
    uv: 3490,
    pv: 4300,
    amt: 2100,
  },
];

// Loading average reward by time dataframe.

export default function AverageRewardByTime(props) {
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
  }, [theDataset])

  return (
    <ResponsiveContainer width="100%" height="100%">
        <LineChart
          width={500}
          height={300}
          data={resultDf}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" />
          <YAxis />
          <Tooltip />
          <Legend />
          {
            groups.map((group, index) => {
              return <Line key = {index} type="monotone" dataKey={group} activeDot={{ r: 8 }} />
            })
          }
        </LineChart>
    </ResponsiveContainer>
  );
}
