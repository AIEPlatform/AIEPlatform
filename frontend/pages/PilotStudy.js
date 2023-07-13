import { useRouter } from 'next/router'
import { useState, useEffect } from 'react'
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { Typography } from '@mui/material';
import Select from 'react-select';

const ratings = [
    {
        value: 0,
        label: 0,
    },
    {
        value: 1,
        label: 1,
    },
    {
        value: 2,
        label: 2,
    },
    {
        value: 3,
        label: 3,
    },
    {
        value: 4,
        label: 4,
    },
    {
        value: 5,
        label: 5,
    }
];

export default function PilotStudy() {
    // load question:
    const router = useRouter();
    let topic = router.query.topic;
    const [question, sQuestion] = useState(null);
    const [username, sUsername] = useState(null);
    const [usernameInput, sUsernameInput] = useState(null);
    const [whichStudy, sWhichStudy] = useState(null);
    const [contextualValue, sContextualValue] = useState(null);
    const [variableName, sVariableName] = useState(null);
    const [treatment, sTreatment] = useState(null);
    const [done, sDone] = useState(false);
    const [quizAnswer, sQuizAnswer] = useState(null);
    const [score, sScore] = useState(null);
    const loadQuestion = () => {
        if (router.query.topic === null || username === null) return;
        fetch(`/apis/pilotStudy/loadQuestion/${router.query.topic}`)
            .then(res => res.json())
            .then(data => {
                sQuestion(data['question']);
            }
            );
    }

    const submitQuizAnswer = () => {
        // send quiz answer
        if (quizAnswer == null) {
            alert("Please select an answer!")
        }
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({
            "topic": router.query.topic,
            "study": whichStudy,
            "username": username,
            "choice": quizAnswer
        });

        var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };

        fetch("/apis/pilotStudy/giveReward", requestOptions)
            .then(response => response.json())
            .then(result => {
                if (result.status_code == 200) {
                    sScore(result['score']);
                }
            })
            .catch(error => console.log('error', error));
    }

    const loadTreatment = () => {
        if (router.query.topic === null || username === null) return;
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({
            "deployment": "Pilot Study",
            "study": whichStudy,
            "user": username,
            "where": router.query.topic
        });

        var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };

        fetch("/apis/treatment", requestOptions)
            .then(response => response.json())
            .then(result => sTreatment(result['treatment']['content']))
            .catch(error => console.log('error', error));
    }

    const loadWhichStudy = (username) => {
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        const raw = JSON.stringify({
            "deployment": "Pilot Study",
            "study": "Numeric Or Text Contextual",
            "user": username
        });

        const requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };
        fetch("/apis/treatment", requestOptions)
            .then(response => response.json())
            .then(result => {
                if (result["status_code"] === 200) {
                    sWhichStudy(result["treatment"]["content"]);
                    if (result["treatment"]["content"] === "numeric") sVariableName("understanding_rating");
                    else sVariableName("understanding");


                    // loadDoneOrNoe
                    var requestOptions = {
                        method: 'GET',
                        redirect: 'follow'
                    };

                    fetch(`/apis/pilotStudy/checkDoneOrNot?topic=${router.query.topic}&study=${result["treatment"]["content"]}&username=${username}`, requestOptions)
                        .then(response => response.json())
                        .then(result => {
                            if(result['status_code'] == 200) {
                                sDone(result['done'])
                            }
                            else {
                                alert("Something is wrong. Please try again later.")
                            }
                        })
                        .catch(error => console.log('error', error));
                }
            })
            .catch(error => alert("Something is wrong, please try again later!"));
    }

    useEffect(() => {
        // load question
        // get username from local storage
        if(router.query.topic == null) return;
        let username = localStorage.getItem("dataarrowPilotStudyUsername") // null
        if (username !== null) {
            sUsername(username);
            loadWhichStudy(username);
        }
    }, [router.query.topic]);

    const submitContextual = () => {
        if (contextualValue == null) {
            alert("Please describe your understanding first!")
        }
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        var raw = JSON.stringify({
            "deployment": "Pilot Study",
            "study": whichStudy,
            "user": username,
            "variableName": variableName,
            "where": router.query.topic,
            "value": contextualValue
        });

        var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow'
        };

        fetch("/apis/variable", requestOptions)
            .then(response => response.json())
            .then(result => {
                if (result['status_code'] == 200) {
                    // display the quiz.
                    loadQuestion();
                    loadTreatment();
                }
            })
            .catch(error => console.log('error', error));
    }
    if (done === false) {
        return (
            <Box sx={{ m: 3 }}>
                <Typography sx={{ mb: 2 }} variant='h6'>Topic: {router.query.topic}</Typography>
                {username === null &&
                    <Box>
                        <Typography variant='p'>Please enter your name:</Typography>
                        <Box><TextField id="outlined-basic" label="Name" variant="outlined" onChange={(event) => { sUsernameInput(event.target.value) }} /></Box>
                        <Button sx={{ mt: 2 }} onClick={() => {
                            sUsername(usernameInput);
                            localStorage.setItem('dataarrowPilotStudyUsername', usernameInput);
                            loadWhichStudy(usernameInput);
                        }} variant='contained'>Submit</Button>
                    </Box>
                }

                {username !== null && question === null && whichStudy &&
                    <Box>
                        {whichStudy === "text" && <TextField
                            id="outlined-multiline-flexible"
                            label="Please write your understanding of the topic."
                            multiline
                            maxRows={4}
                            fullWidth={true}
                            minRows={5}
                            onChange={(event) => { sContextualValue(event.target.value) }}
                        />}
                        {whichStudy === "numeric" &&
                            <Select
                                className="basic-single"
                                classNamePrefix="select"
                                name="understanding"
                                options={ratings}
                                onChange={(event) => { sContextualValue(event.value) }}
                            />
                        }

                        <Button sx={{ mt: 2 }} onClick={submitContextual} variant='contained'>Submit</Button>
                    </Box>}
                {treatment === "concept_first" &&
                    <Box>
                        <mark><a href = {question['concept']}> Material To Read</a></mark>
                    </Box>}
                {question !== null && username !== null && contextualValue !== null &&
                    <FormControl>
                        <FormLabel id="demo-radio-buttons-group-label">{question['question']}</FormLabel>
                        <RadioGroup
                            aria-labelledby="demo-radio-buttons-group-label"
                            name="radio-buttons-group"
                            onChange={(event) => { sQuizAnswer(event.target.value) }}

                        >
                            {/* iterate over question['choices'], which is an array */}

                            {
                                question['choices'].map((choice, index) => {
                                    return (
                                        <FormControlLabel disabled={score !== null} key={index} value={index} control={<Radio />} label={choice} />
                                    )
                                }
                                )
                            }
                        </RadioGroup>
                        <Button sx={{ m: 2 }} variant="contained" onClick={submitQuizAnswer} disabled={score !== null}>Submit</Button>
                    </FormControl>
                }
                {score !== null && <Box>Your answer got a score {score}</Box>}
                {score != null && treatment === "concept_later" &&
                    <Box>
                        <mark><a href = {question['concept']}> Material To Read</a></mark>
                    </Box>}
            </Box>
        )
    }
    else if(done === true) {
        return (
            <Box sx={{ m: 3 }}>
                Your are done for this topic ({router.query.topic}). Thanks for your participation!
            </Box>
        )
    }
    else {
        return (
            <Box sx={{ m: 3 }} />
        )
    }
}