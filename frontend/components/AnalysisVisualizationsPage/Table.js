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
import { Typography } from '@mui/material';

function ChooseDataset(props) {
  let datasets = props.datasets;
  let sSelectedDataset = props.sSelectedDataset;
  let sContextuals = props.sContextuals;
  let sSelectedContextual = props.sSelectedContextual;
  let handleChooseDataset = (option) => {
    sSelectedDataset(datasets[option['value']]);
    sSelectedContextual(null);
    fetch(`/apis/analysis_default_table/get_contextual_variables?datasetDescription=${datasets[option['value']]['datasetDescription']}`).then(res => res.json()).then(data => {
      if (data['status_code'] === 200)
        sContextuals(['no contextual', ...data['data']]);
    })
  }
  const options = datasets.map((dataset, index) => ({
    value: index,
    label: `${dataset.datasetDescription} - ${dataset.mooclet} - 20230518`
  }));
  return (
    <Select options={options} value={props.selectedDataset ? options[datasets.indexOf(props.selectedDataset)] : null}
      onChange={(option) => {
        handleChooseDataset(option)
      }}
    />
  )
}


function ChooseContextual(props) {
  let contextuals = props.contextuals;
  let sSelectedContextual = props.sSelectedContextual;
  let selectedDataset = props.selectedDataset;
  let sRows = props.sRows;
  let sColumns = props.sColumns;
  let handleChooseDataset = (option) => {
    sSelectedContextual(contextuals[option['value']]);
    console.log(props.selectedDataset)
    fetch(`/apis/analysis_default_table?datasetDescription=${props.selectedDataset['datasetDescription']}&contextualVariable=${contextuals[option['value']]}`).then(res => res.json()).then(data => {
      sRows(data['rows'])
      sColumns(data['columns'])
    })
  }
  const options = contextuals.map((contextual, index) => ({
    value: index,
    label: contextual
  }));
  return (
    <Select options={options} value={props.selectedContextual ? options[contextuals.indexOf(props.selectedContextual)] : null}
      onChange={(option) => {
        handleChooseDataset(option)
      }}
    />
  )
}

// function createData(name, calories, fat, carbs, protein) {
//   return { name, calories, fat, carbs, protein };
// }

// const rows = [
//   createData('Frozen yoghurt', 159, 6.0, 24, 4.0),
//   createData('Ice cream sandwich', 237, 9.0, 37, 4.3),
//   createData('Eclair', 262, 16.0, 24, 6.0),
//   createData('Cupcake', 305, 3.7, 67, 4.3),
//   createData('Gingerbread', 356, 16.0, 49, 3.9),
// ];

export default function BasicTable(props) {

  const theDataset = props.theDataset;
  const [selectedVariables, sSelectedVariables] = useState([]);

  const [columns, sColumns] = useState([]);
  const [rows, sRows] = useState([]);

  const getTable = (selectedVariables) => {
    fetch('/apis/analysis/basic_reward_summary_table', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        theDatasetId: theDataset['_id']['$oid'],
        selectedVariables: selectedVariables
      })
    })
      .then(res => res.json())
      .then(data => {
        sColumns(data['result']['columns']);
        sRows(data['result']['rows']);
      })
      .catch(err => console.log(err))
  }

  React.useEffect(() => {
    // Get the very basic A/B test info without any contextual variables
    // make a post request to the backend
    if (theDataset == null) {
      return;
    }
    else {
      getTable([]);
    }
  }, [theDataset]);


  const shouldMergeCells = (rowIndex, columnIndex) => {
    // Add your logic here to determine if cells should be merged
    // For example, you can compare adjacent cells or check certain conditions in the data
    return rowIndex > 0 && rows[rowIndex][columnIndex] === rows[rowIndex - 1][columnIndex];
  };

  return (
    <Container style={{ maxHeight: "100%", display: 'flex', flexDirection: 'column' }}>
      <Select
        isMulti
        options={theDataset ? theDataset['variables'].map((variable, index) => ({
          value: index,
          label: variable
        })) : []}
        onChange={(options) => {
          sSelectedVariables(options.map(option => option['label']));
          getTable(options.map(option => option['label']));
        }}
      />
      <TableContainer component={Paper} style={{ marginTop: "2em", flex: '1', overflowY: 'auto' }}>
        <Table aria-label="simple table">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell>{column}</TableCell>
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
