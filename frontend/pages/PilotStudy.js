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
    const router = useRouter()

    const [question, sQuestion] = useState(null);
    const [username, sUsername] = useState(null);
    const [usernameInput, sUsernameInput] = useState(null);
    const [whichStudy, sWhichStudy] = useState(null);
    const [contextualValue, sContextualValue] = useState(null);
    const [variableName, sVariableName] = useState(null);
    const [treatment, sTreatment] = useState(null);
    const [done, sDone] = useState(false);
    const [quizAnswer, sQuizAnswer] = useState(null);
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

        fetch("/apis/get_treatment", requestOptions)
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
        fetch("/apis/get_treatment", requestOptions)
            .then(response => response.json())
            .then(result => {
                if (result["status_code"] === 200) {
                    sWhichStudy(result["treatment"]["content"]);
                    if (result["treatment"]["content"] === "numeric") sVariableName("understanding_rating");
                    else sVariableName("understanding");
                }
            })
            .catch(error => alert("Something is wrong, please try again later!"));
    }

    useEffect(() => {
        // load question
        // get username from local storage
        let username = localStorage.getItem("dataarrowPilotStudyUsername") // null
        if (username !== "null") {
            sUsername(username);
            loadWhichStudy(username);
        }
    }, []);

    const submitContextual = () => {
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

        fetch("/apis/give_variable", requestOptions)
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
    return (
        <div>
            <h1>Pilot Study</h1>
            {treatment}
            <h2>Topic: {router.query.topic}</h2>
            {username !== null && <h2>Welcome back: {username}</h2>}
            {username === null &&
                <div>
                    <h2>Please enter your name:</h2>
                    <TextField id="outlined-basic" label="Name" variant="outlined" onChange={(event) => { sUsernameInput(event.target.value) }} />
                    <Button onClick={() => {
                        sUsername(usernameInput);
                        localStorage.setItem('dataarrowPilotStudyUsername', usernameInput);

                        loadWhichStudy();
                    }}>Submit</Button>
                </div>
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
                        <TextField
                            id="outlined-select-currency-native"
                            select
                            label="Please rate your understanding of the topic."
                            fullWidth={true}
                            SelectProps={{
                                native: true,
                            }}
                            onChange={(event) => { sContextualValue(event.target.value) }}
                        >
                            {ratings.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </TextField>
                    }

                    <Button onClick={submitContextual}>Submit my self-reporting understanding on the topic.</Button>
                </Box>}
            {done === false && treatment === "concept_first" &&
                <Box>
                    <mark>{question['concept']}</mark>
                </Box>}
            {question !== null && username !== null && contextualValue !== null && done === false &&
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
                                    <FormControlLabel disabled={done} key={index} value={index} control={<Radio />} label={choice} />
                                )
                            }
                            )
                        }
                    </RadioGroup>
                    <Button onClick={submitQuizAnswer} disabled={done}>Submit</Button>
                </FormControl>
            }
            {done === true && treatment === "concept_later" &&
                <Box>
                    <mark>{question['concept']}</mark>
                </Box>}
        </div>
    )
}