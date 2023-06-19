import { useEffect, useContext, useState } from 'react';
import { styled, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import MuiAppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import Link from 'next/link';

import AddIcon from '@mui/icons-material/Add';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import DatasetIcon from '@mui/icons-material/Dataset';
import InsightsIcon from '@mui/icons-material/Insights';
import EnhancedEncryptionIcon from '@mui/icons-material/EnhancedEncryption';
import LogoutIcon from '@mui/icons-material/Logout';

import { UserContext } from "../contexts/UserContextWrapper";



const drawerWidth = 250;

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })(
    ({ theme, open }) => ({
        flexGrow: 1,
        padding: theme.spacing(3),
        transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
        }),
        marginLeft: `-${drawerWidth}px`,
        ...(open && {
            transition: theme.transitions.create('margin', {
                easing: theme.transitions.easing.easeOut,
                duration: theme.transitions.duration.enteringScreen,
            }),
            marginLeft: 0,
        }),
    }),
);

const AppBar = styled(MuiAppBar, {
    shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
    transition: theme.transitions.create(['margin', 'width'], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    ...(open && {
        width: `calc(100% - ${drawerWidth}px)`,
        marginLeft: `${drawerWidth}px`,
        transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.easeOut,
            duration: theme.transitions.duration.enteringScreen,
        }),
    }),
}));

const DrawerHeader = styled('div')(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
    justifyContent: 'flex-end',
}));

export default function Layout({ children }) {
    const theme = useTheme();
    const [open, setOpen] = useState(false);
    const { userContext, sUserContext } = useContext(UserContext);

    const handleDrawerOpen = () => {
        setOpen(true);
    };

    const handleDrawerClose = () => {
        setOpen(false);
    };

    const handleLogout = () => {
        fetch('/apis/auth/logout')
            .then(res => res.json())
            .then(data => {
                if (data['status'] === 200) {
                    sUserContext(null);
                    console.log(userContext)
                }
            })
    }


    const links = ['My Deployment', 'New Deployment', 'Data Workshop', 'Analysis & Visualizations'];
    const linkURLs = ['/', '/NewDeployment', '/DataWorkshop', '/AnalysisVisualizations'];
    const icons = [<AutoFixHighIcon />, <AddIcon />, <DatasetIcon />, <InsightsIcon />]

    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar position="fixed" open={open}>
                <Toolbar>
                    {userContext !== undefined && userContext !== null && <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        onClick={handleDrawerOpen}
                        edge="start"
                        sx={{ mr: 2, ...(open && { display: 'none' }) }}
                    >
                        <MenuIcon />
                    </IconButton>}
                    <Typography variant="h6" noWrap component="div">
                        DataArrow
                    </Typography>
                </Toolbar>
            </AppBar>
            {userContext !== undefined && userContext !== null &&
                <Drawer
                    sx={{
                        width: drawerWidth,
                        flexShrink: 0,
                        '& .MuiDrawer-paper': {
                            width: drawerWidth,
                            boxSizing: 'border-box',
                        },
                    }}
                    variant="persistent"
                    anchor="left"
                    open={open}
                >
                    <DrawerHeader>
                        <IconButton onClick={handleDrawerClose}>
                            {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                        </IconButton>
                    </DrawerHeader>
                    <Typography variant='h6' style={{ textAlign: "center" }}>My experiments</Typography>
                    <Divider />
                    <List>
                        {links.map((text, index) => (
                            <Link key={index} href={linkURLs[index]} style={{ textDecoration: 'none', color: 'black' }}>
                                <ListItem key={index} disablePadding>
                                    <ListItemButton>
                                        {icons[index]} <Typography sx={{ ml: 1 }}>{links[index]}</Typography>
                                    </ListItemButton>
                                </ListItem>
                            </Link>
                        ))}
                    </List>
                    <Divider />
                    <Typography variant='h6' style={{ textAlign: "center" }}>My account</Typography>
                    <Box>
                        <Link href='/ChangePassword' style={{ textDecoration: 'none', color: 'black' }}>
                            <ListItem key="change-password" disablePadding>
                                <ListItemButton>
                                    <EnhancedEncryptionIcon /> <Typography sx={{ ml: 1 }}>Change My Password</Typography>
                                </ListItemButton>
                            </ListItem>
                        </Link>

                        <ListItem key="logout" onClick={() => handleLogout()} disablePadding>
                            <ListItemButton>
                                <LogoutIcon /> <Typography sx={{ ml: 1 }}>Logout</Typography>
                            </ListItemButton>
                        </ListItem>
                    </Box>
                </Drawer>}
            <Main open={open}>
                <DrawerHeader />
                {<main>{children}</main>}
            </Main>
        </Box>
    );
}