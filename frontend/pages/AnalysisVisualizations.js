import { React, useContext, useState, useEffect } from 'react';
import { Container, Typography, Box, Button, Paper } from '@mui/material';
import Layout from '../components/layout';
import Select from 'react-select';
import Head from 'next/head';
import AverageRewardByTime from "../components/AnalysisVisualizationsPage/AverageRewardByTime";
import Table from "../components/AnalysisVisualizationsPage/Table";
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry"
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import UpgradeIcon from '@mui/icons-material/Upgrade';

import { UserContext } from "../contexts/UserContextWrapper";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

const availableAnalysises = [
  {
    value: 'basicRewardTable',
    label: 'Basic Reward Table',
  },
  {
    value: 'averageRewardByTime',
    label: 'Average Reward By Time',
  }
];


export default function DataAnalysis(props) {

  const { userContext, sUserContext } = useContext(UserContext);
  // if userContext is not null, redirects to dashboard.
  useEffect(() => {
    if (userContext !== undefined && userContext === null) {
      window.location.href = "/Login";
    }
  }, [userContext]);

  const [myDeployments, sMyDeployments] = useState([]);
  const [theDatasets, sTheDatasets] = useState([]);
  const [theDataset, sTheDataset] = useState(null);
  const [datasetTime, sDatasetTime] = useState(0);
  const [theDeployment, sTheDeployment] = useState(null);

  const [analysises, sAnalysises] = useState([]);
  const [newAnalysis, sNewAnalysis] = useState(null);

  const handleDrop = (droppedItem) => {
    // Ignore drop outside droppable container
    if (!droppedItem.destination) return;
    var updatedList = [...analysises];
    // Remove dragged item
    const [reorderedItem] = updatedList.splice(droppedItem.source.index, 1);
    // Add dropped item
    updatedList.splice(droppedItem.destination.index, 0, reorderedItem);
    // Update State
    sAnalysises(updatedList);
  };

  useEffect(() => {
    fetch('/apis/my_deployments')
      .then(response => response.json())
      .then(data => {
        sMyDeployments(data["my_deployments"]);
      });

    const items = JSON.parse(localStorage.getItem('analysises'));
    if (items) {
      sAnalysises(items);
    }
    else {
      localStorage.setItem('analysises', JSON.stringify(analysises));
    }

    const deployment = JSON.parse(localStorage.getItem('theDeployment'));
    if (deployment) {
      sTheDeployment(deployment);
    }

    const dataset = JSON.parse(localStorage.getItem('theDataset'));
    if (dataset) {
      sTheDataset(dataset);
    }

    handleSelectMyDeployment(deployment);
  }, []);


  useEffect(() => {
    localStorage.setItem('analysises', JSON.stringify(analysises));
  }, [analysises]);

  useEffect(() => {
    localStorage.setItem('theDeployment', JSON.stringify(theDeployment));
    localStorage.setItem('theDataset', JSON.stringify(theDataset));
    // TODO: Maybe not to remove all analysises? keep the types but remove the data?
  }, [theDeployment, theDataset]);


  const resetAnalysises = () => {
    let data = [...analysises];

    const filteredArray = data.map(obj => {
      const filteredObject = {};
      ['label', 'value'].forEach(field => {
        filteredObject[field] = obj[field];
      });
      return filteredObject;
    });
    sAnalysises(filteredArray);
    localStorage.setItem('analysises', JSON.stringify(filteredArray));
  }

  const handleSelectMyDeployment = (option) => {
    fetch(`/apis/analysis/get_deployment_datasets?deployment=${option["name"]}`)
    .then(response => response.json())
    .then(data => {
      sTheDatasets(data["datasets"]);
      sTheDeployment(option);
    });
  }


  const handleDatasetDelete = () => {
    // /apis/analysis/deleteArrowDataset/<id>" DELETE
    if (theDataset) {
      fetch(`/apis/analysis/deleteArrowDataset/${theDataset['_id']['$oid']}`, { method: "DELETE" })
        .then(response => response.json())
        .then(data => {
          if (data["status"] === 200) {
            alert("Dataset deleted.");
            window.location.reload();
          }
          else {
            alert("Error: " + data["message"]);
          }
        });
    }
  }

  const handleDatasetUpdate = () => {
    if (theDataset) {
      fetch(`/apis/analysis/updateArrowDataset/${theDataset['_id']['$oid']}`, { method: "PUT" })
        .then(response => response.json())
        .then(data => {
          if (data["status"] === 200) {
            // alert("Dataset Updated.");
            // Replace the dataset with the new returned one.
            sDatasetTime(datasetTime + 1)
          }
          else {
            alert("Error: " + data["message"]);
          }
        });
    }
  }

  const [csvFile, setCsvFile] = useState(null);

  const handleCsvUpload = (event) => {
    const file = event.target.files[0];
    setCsvFile(file);
  };


  const handleFileUpload = () => {
    const formData = new FormData();
    formData.append('csvFile', csvFile);
    formData.append('datasetId', theDataset['_id']['$oid']);

    fetch('/apis/upload_local_modification', {
      method: 'PUT',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data['status'] === 200) {
          window.location.reload();
        }
        else {
          alert("Error: " + data["message"]);
        }
      }
      )
      .catch(error => {
        console.error('Error uploading file:', error);
      });
  };

  const handleAddNewAnalysis = () => {
    let data = [...analysises];
    // get how many same types there are
    let count = 0;
    for (const element of data) {
      if (element['type'] === newAnalysis['type']) {
        count++;
      }
    }

    const toAdd = JSON.parse(JSON.stringify(newAnalysis));
    toAdd['value'] = `${toAdd['value']}_${count + 1}` // TODO: Come up with a better solution to distinguish different analysises with same type.
    data.push(toAdd);
    sAnalysises(data);
  }

  const handleDeleteAnalysis = (item) => {
    let analysisId = item['value'];
    let data = [...analysises];
    data = data.filter((element) => element['value'] !== analysisId);
    sAnalysises(data);
  }

  if (userContext !== undefined && userContext !== null) {
    return (
      <Layout>
        <Head><title>Data Analysis - DataArrow</title></Head>
        <Container maxWidth="md">
          <Typography variant="p" align="center" sx={{ mb: 3 }}><strong>Disclaimer: the analysis & visualizations are for insights only. Please conduct a more rigor analysis to get a better understanding of your data.</strong></Typography>
          <Box sx={{ mb: 3 }}>
            <Typography variant="p">Deployment: </Typography>
            <Select
              options={myDeployments}
              getOptionLabel={(option) => option["name"]}
              getOptionValue={(option) => option["_id"]["$oid"]}
              onChange={(option) => {
                handleSelectMyDeployment(option)
                resetAnalysises();
              }}
              value={theDeployment}
            />
          </Box>


          <Box sx={{ mb: 3 }}>
            <Typography variant="p">Dataset: </Typography>
            <Select
              options={theDatasets}
              getOptionLabel={(option) => `${option['study']}: ${option["name"]}`}
              getOptionValue={(option) => option["_id"]["$oid"]}
              value={theDataset}
              onChange={(option) => {
                sTheDataset(option);
                resetAnalysises();
              }}
            />
          </Box>

          {theDataset && <Box sx={{ m: 3, ml: 0 }}>
            <Button sx={{ m: 2, ml: 0 }} variant="contained" href={`/apis/analysis/downloadArrowDataset/${theDataset['_id']['$oid']}`}><DownloadIcon></DownloadIcon>Download</Button>
            <Button sx={{ m: 2, ml: 0 }} variant="contained" color="error" onClick={handleDatasetDelete}><DeleteIcon></DeleteIcon>Delete</Button>

            <Button sx={{ m: 2, ml: 0 }} variant="contained" color="error" onClick={handleDatasetUpdate}><UpgradeIcon></UpgradeIcon>Update</Button>

            {theDataset && <Box>
              <Typography>ADVANCED: you can choose to work on the dataset locally, and re-upload the updated dataset, which will then replace the dataset in the cloud. KEEP IN MIND that this operation is not undoable!</Typography>
              <label htmlFor="csv-upload">Upload CSV file:</label>
              <input
                id="csv-upload"
                type="file"
                accept=".csv"
                onChange={handleCsvUpload}
              />
              {csvFile && <p>File selected: {csvFile.name}</p>}
              {csvFile && <button onClick={handleFileUpload}>Upload</button>}
            </Box>}
          </Box>}

          <Box sx={{ m: 3, ml: 0 }}>
            <DragDropContext onDragEnd={handleDrop}>
              <Droppable droppableId="list-container">
                {(provided) => (
                  <div
                    className="list-container"
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                  >
                    {analysises.map((item, index) => (
                      <Draggable key={item['value']} draggableId={item['value']} index={index}>
                        {(provided) => (
                          <div
                            className="item-container"
                            ref={provided.innerRef}
                            {...provided.dragHandleProps}
                            {...provided.draggableProps}
                          >
                            {item['label']}
                            <Button onClick={() => handleDeleteAnalysis(item)}>X</Button>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
            <Typography variant="p">New Analysis: </Typography>
            <Select
              options={availableAnalysises}
              onChange={(option) => {
                sNewAnalysis(option);
              }}
            />
            <Button sx={{ m: 2, ml: 0 }} variant="contained" color="success" onClick={() => handleAddNewAnalysis()}>Add</Button>
          </Box>

        </Container>

        <ResponsiveMasonry
          columnsCountBreakPoints={{ 350: 1, 750: 2 }}
        >
          <Masonry>
            {/* <Paper style={{ width: '100%', height: '300px' }}>
              <AverageRewardByTime theDataset={theDataset} datasetTime={datasetTime} style={{ position: "fixed", width: "100vw", height: "100vh" }} />
            </Paper> */}
            {/* 
            <Paper sx={{ m: 2, p: 2 }} style={{ maxWidth: '100%', maxHeight: '500px' }}>
              <Table theDataset={theDataset} datasetTime={datasetTime} />
            </Paper>

            <Paper sx={{ m: 2, p: 2 }} style={{ maxWidth: '100%', maxHeight: '500px' }}>
              <Table theDataset={theDataset} datasetTime={datasetTime} />
            </Paper>

            <Paper sx={{ m: 2, p: 2 }} style={{ maxWidth: '100%', maxHeight: '500px' }}>
              <Table theDataset={theDataset} datasetTime={datasetTime} />
            </Paper> */}
            {analysises.map((item, index) => (
              <Paper key = {item['value']} sx={{ m: 2, p: 2 }} style={{ maxWidth: '100%', maxHeight: '500px' }}>
                {item['label'] == 'Basic Reward Table' && <Table theDataset={theDataset} datasetTime={datasetTime} analysis={item} sAnalysises={sAnalysises} analysises={analysises}/>}
                {item['label'] == 'Average Reward By Time' && <AverageRewardByTime theDataset={theDataset} datasetTime={datasetTime} analysis={item} sAnalysises={sAnalysises} analysises={analysises}/>}
              </Paper>
            ))}
          </Masonry>
        </ResponsiveMasonry>

      </Layout>
    );
  }
}
