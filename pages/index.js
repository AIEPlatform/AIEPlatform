import * as React from 'react';
import { useEffect } from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Layout from '../components/layout';
import Head from 'next/head';

export default function Index() {
  return (
    <Layout>
      <Head>
        <title>DataArrow</title>
      </Head>
      <Typography>Welcome to Dashboard!</Typography>
      <Typography>To register your access, please visit: /signUpMOOCletToken/:accessCode</Typography>
    </Layout>
  );
}
