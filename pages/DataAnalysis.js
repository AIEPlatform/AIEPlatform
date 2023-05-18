import * as React from 'react';
import { Container, Typography } from '@mui/material';
import Layout from '../components/layout';
import Head from 'next/head';
import SimpleLineChart from "../components/DataAnalysisPage/SimpleLineChart";
import Table from "../components/DataAnalysisPage/Table";
import { Grid } from '@mui/material';
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry"


export default function DataAnalysis(props) {


  return (
    <Layout>
      <Head><title>Data Analysis - MOOClet Dashboard</title></Head>
      {/* <Container style={{ maxWidth: '50%', height: '270px' }}>
        <SimpleLineChart width="200px" height="200px"></SimpleLineChart>
      </Container> */}
      <ResponsiveMasonry
        columnsCountBreakPoints={{ 350: 1, 750: 2}}
      >
        <Masonry>
          <div style={{ width: '100%', height: '300px' }}>
            <SimpleLineChart style = {{position: "fixed", width: "100vw", height: "100vh"}}/>
            {/* Content for the first div */}
          </div>

          <div style={{ maxWidth: '100%', maxHeight: '500px' }}>
            <Table />
            {/* Content for the first div */}
          </div>
          <div style={{ maxWidth: '100%', height: '400px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>

          <div style={{ maxWidth: '100%', height: '700px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>
          <div style={{ maxWidth: '100%', height: '100px' }}>
            Test
          </div>
          <div style={{ maxWidth: '100%', height: '200px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>
          <div style={{ maxWidth: '100%', height: '200px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>
          <div style={{ maxWidth: '100%', height: '200px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>
          <div style={{ maxWidth: '100%', height: '200px' }}>
            <SimpleLineChart />
            {/* Content for the first div */}
          </div>
        </Masonry>
      </ResponsiveMasonry>
    </Layout>
  );
}
