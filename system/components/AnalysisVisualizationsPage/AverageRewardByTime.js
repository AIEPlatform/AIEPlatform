// load useEffect
import React, { useEffect, useState } from 'react';
import Container from '@mui/material/Container';
import { Stack, Typography, IconButton } from '@mui/material';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ErrorBar } from 'recharts';
import Select from 'react-select';

// Loading average reward by time dataframe.

const distinctColors = ["red", "blue", "green", "orange", "purple", "pink", "cyan", "magenta", "teal"];

export default function AverageRewardByTime(props) {

  const theDataset = props.theDataset;
  const analysis = props.analysis;
  const analysises = props.analysises;
  const sAnalysises = props.sAnalysises;
  const closeButtonClickHandler = props.closeButtonClickHandler;

  const [resultDf, sResultDf] = useState([]);
  const [groups, sGroups] = useState([]);
  const getGraph = () => {
    fetch('/apis/analysis/AverageRewardByTime', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        theDatasetId: theDataset['_id']['$oid'], 
        selectedAssigners: analysis['selectedAssigners'] ? analysis['selectedAssigners'].map((variable) => variable['value']): [],
        selectedVersions: analysis['selectedVersions'] ? analysis['selectedVersions'].map((variable) => variable['value']): []
      })
    })
      .then(res => res.json())
      .then(data => {
        sResultDf(data['data']);
        sGroups(data['groups']);
      })
      .catch(err => console.log(err))
  }
  useEffect(() => {
    if (theDataset == null) return;
    getGraph();
  }, [theDataset, props.datasetTime])

  useEffect(() => {
    if(!analysis['selectedVersions']) {
      analysis['selectedVersions'] = [];
    }
    if(!analysis['selectedAssigners']) {
      analysis['selectedAssigners'] = [];
    }
    sAnalysises([...analysises]);
  }, [analysis])


  useEffect(() => {
    // Get the very basic A/B test info without any contextual variables
    // make a post request to the backend
    if (theDataset == null) {
      return;
    }
    else {
      getGraph();
    }
  }, [theDataset, props.datasetTime, analysis['selectedVersions'], analysis['selectedAssigners']]);

  return (
    <>
      <Container style={{ maxHeight: "100%", display: 'flex', flexDirection: 'column' }}>
        <Stack direction="row" justifyContent="space-between">
          <Typography variant='h6'>Average Reward as a function of time</Typography>
          <IconButton onClick={() => closeButtonClickHandler(analysis)}>
            <CloseOutlinedIcon />
          </IconButton>
        </Stack>

        <Typography variant="p">Choose a policy</Typography>
        <Select
          isMulti
          options={theDataset ? theDataset['assigners'].map((assigner, index) => ({
            value: assigner,
            label: assigner
          })) : []}
          value={analysis['selectedAssigners']}
          onChange={(options) => {
            analysis['selectedAssigners'] = options;
            sAnalysises([...analysises]);
          }}
        />
        <Typography variant="p">Choose a version</Typography>
        <Select
          isMulti
          options={theDataset ? theDataset['versions'].map((version, index) => ({
            value: version,
            label: version
          })) : []}
          value={analysis['selectedVersions']}
          onChange={(options) => {
            analysis['selectedVersions'] = options;
            sAnalysises([...analysises]);
          }}
        />
      </Container>

      <div style={{ maxWidth: '100%', height: '500px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={resultDf}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" />
            <YAxis label={{ value: "Reward", position: "insideLeft", angle: -90 }} />

            <Tooltip />
            <Legend />
            {
              groups.map((group, index) => {
                if (group.includes('errorBar')) return;
                return (
                  <Line key={group} type="monotone" dataKey={group} stroke={distinctColors[index % 9]} activeDot={{ r: 8 }}>
                    <ErrorBar dataKey={`${group}-errorBar`} width={4} strokeWidth={2} stroke={distinctColors[index % 9]} direction="y" />
                  </Line>
                )
              })
            }
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
