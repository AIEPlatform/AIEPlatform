import { React, useContext, useState, useEffect } from 'react';
import { Typography, Paper, TextField, Box, Grid, Divider, Button, Container } from '@mui/material';
import Link from '@mui/material/Link';
import Layout from '../components/layout';
import Head from 'next/head';
import { UserContext } from "../contexts/UserContextWrapper";

function NewDeployment() {
    const { userContext, sUserContext } = useContext(UserContext);
    useEffect(() => {
        if (userContext !== undefined && userContext === null) {
            window.location.href = "/Login";
        }
    }, [userContext]);


    const handleSubmit = (event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        console.log({
          currentPassword: data.get('current-password'),
          newPassword: data.get('new-password'),
        });
        //@auth_apis.route("/apis/auth/changePassword", methods=["PUT"])
        fetch('/apis/auth/changePassword', {
            method: 'PUT',
            body: JSON.stringify({
                currentPassword: data.get('current-password'),
                newPassword: data.get('new-password'),
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                if (data["status"] == 200) {
                    alert("Password changed successfully!");
                } else {
                    alert(data['message']);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                alert("something went wrong.")
            }
            );
      };


    if (userContext !== undefined && userContext !== null) {
        return (
            <Layout>
                <Head><title>New Deployment - DataArrow</title></Head>
                <Container>
                    <Box component="form" noValidate onSubmit={handleSubmit} sx={{ mt: 3 }}>
                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <TextField
                                    required
                                    fullWidth
                                    name="current-password"
                                    label="Current Password"
                                    type="password"
                                    id="current-password"
                                />
                            </Grid>
                        </Grid>

                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <TextField
                                    required
                                    fullWidth
                                    name="new-password"
                                    label="New Password"
                                    type="password"
                                    id="new-password"
                                />
                            </Grid>
                        </Grid>
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            sx={{ mt: 3, mb: 2 }}
                        >
                            Change
                        </Button>
                    </Box>
                </Container>

            </Layout>
        );
    }
}


export default NewDeployment;