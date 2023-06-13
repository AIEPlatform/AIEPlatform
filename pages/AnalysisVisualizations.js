import { React, use, useState, useEffect } from 'react';
import { Container, Typography, Box } from '@mui/material';
import Select from 'react-select';
import Layout from '../components/layout';
import Head from 'next/head';
import AverageRewardByTime from "../components/AnalysisVisualizationsPage/AverageRewardByTime";
import Table from "../components/AnalysisVisualizationsPage/Table";
import { Grid } from '@mui/material';
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry"


export default function DataAnalysis(props) {

  const [myDeployments, sMyDeployments] = useState([]);
  const [theDatasets, sTheDatasets] = useState([]);
  const [theDataset, sTheDataset] = useState(null);

  useEffect(() => {
    fetch('/apis/my_deployments')
      .then(response => response.json())
      .then(data => {
        sMyDeployments(data["my_deployments"]);
      });
  }, []);

  const handleSelectMyDeployment = (option) => {
    fetch(`/apis/analysis/get_deployment_datasets?deployment=${option["name"]}`)
      .then(response => response.json())
      .then(data => {
        sTheDatasets(data["datasets"]);
      });
  }



  return (
    <Layout>
      <Head><title>Data Analysis - DataArrow</title></Head>
      <Container maxWidth="md">
        <Box sx={{ mb: 3 }}>
          <Typography variant="p">Deployment: </Typography>
          <Select
            options={myDeployments}
            getOptionLabel={(option) => option["name"]}
            getOptionValue={(option) => option["_id"]["$oid"]}
            onChange={(option) => handleSelectMyDeployment(option)}
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
            }}
          />
        </Box>
        <Typography variant="p" align="center" sx={{ mb: 3 }}><strong>Disclaimer: the analysis & visualizations are for insights only. Please conduct a more rigor analysis to get a better understanding of your data.</strong></Typography>
      </Container>

      <ResponsiveMasonry
        columnsCountBreakPoints={{ 350: 1, 750: 2 }}
      >
        <Masonry>
          <div style={{ width: '100%', height: '300px' }}>
            <AverageRewardByTime theDataset = {theDataset} style={{ position: "fixed", width: "100vw", height: "100vh" }} />
            {/* Content for the first div */}
          </div>

          <div style={{ maxWidth: '100%', maxHeight: '500px' }}>
            <Table theDataset = {theDataset} />
            {/* Content for the first div */}
          </div>
        </Masonry>
      </ResponsiveMasonry>
    </Layout>
  );
}
