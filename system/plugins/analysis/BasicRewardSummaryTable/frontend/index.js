import * as React from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Container from '@mui/material/Container';
import Select from 'react-select';
import { useEffect, useState } from 'react';
import { Stack, Typography, IconButton } from '@mui/material';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';

export const name = "Basic Reward Summary Table";

export function main(props) {

  const theDataset = props.theDataset;
  const analysis = props.analysis;
  const analysises = props.analysises;
  const sAnalysises = props.sAnalysises;
  const closeButtonClickHandler = props.closeButtonClickHandler;

  const [columns, sColumns] = useState([]);
  const [rows, sRows] = useState([]);

  const getTable = () => {
    fetch('/apis/analysis/analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        theDatasetId: theDataset['_id']['$oid'],
        info: {
          selectedVariables: analysis['selectedVariables'].map((variable) => variable['value']), 
          selectedAssigners: analysis['selectedAssigners'].map((variable) => variable['value'])
        },
        analysisType: 'BasicRewardSummaryTable'
      })
    })
      .then(res => res.json())
      .then(data => {
        sColumns(data['result']['columns']);
        sRows(data['result']['rows']);
      })
      .catch(err => console.log(err))
  }

  useEffect(() => {
    if(!analysis['selectedVariables']) {
      analysis['selectedVariables'] = [];
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
      getTable();
    }
  }, [theDataset, props.datasetTime, analysis['selectedVariables'], analysis['selectedAssigners']]);

  return (
    <Container style={{ maxHeight: "100%", display: 'flex', flexDirection: 'column'}}>
      <Stack direction="row" justifyContent="space-between">
        <Typography variant="h6">Basic Reward Summary Table</Typography>
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
      <Typography variant="p">Choose a variable</Typography>
      <Select
        isMulti
        options={theDataset ? theDataset['variables'].map((variable, index) => ({
          value: variable,
          label: variable
        })) : []}
        value={analysis['selectedVariables']}
        onChange={(options) => {
          analysis['selectedVariables'] = options;
          sAnalysises([...analysises]);
        }}
      />
      <TableContainer component={Paper} style={{ marginTop: "2em", flex: '1', overflowY: 'auto' }}>
        <Table aria-label="simple table">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column}>{column}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, rowIndex) => (
              <TableRow
                key={rowIndex}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                {
                  row.map((cell, columnIndex) => (
                    <TableCell key={columnIndex}>{cell}</TableCell>
                  ))
                }
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
}
