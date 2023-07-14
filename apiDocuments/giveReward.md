
# Give a reward

A user gives a reward. If correct, the system will match the reward with an interaction.

**URL** : `/apis/reward/`

**Method** : `POST`

**Auth required** : OPTIONAL

**Required Request Body**

```json
{
    "deployment": "Name of the deployment",
    "study": "Name of the study",
    "user": "Name of the user",
    "value": "Value of the reward"
}
```

If the deployment for the study has apiToken protection on, the following request body is required:
```json
{
	"apiToken": "apiToken (you can get from the dashboard)"
}
```

**OPTIONAL Request Body**
```json
{
	"where": "The reward will only be possible to append to interaction with same where field.",
	"otherInformation": "JSON OBJECT that contains other information (NOT IN USE)"
}
```



## Success Responses

**Condition** : The deployment and study exists, and api token is given correctly when required. And the user does have an orphan interaction. When `where` is given, this orphan interaction must have the same `where`.

**Code** : `200 OK`

**Content example** : 

```json
{
    "status_code": 200,
    "message": "Reward is saved."
}
```

## Error Response

### Deployment Not Found

**Condition** : The deployment with the given name doesn't exist.

**Code** : `404 NOT FOUND`

**Content example** :

```json
{
    "status_code": 404,
    "message": "Deployment Simulation not found or you don't have permission."
}
```

### Study Not Found

**Condition** : The study with the given name doesn't exist.

**Code** : `404 NOT FOUND`

**Content example** :

```json
{
    "status_code": 404,
    "message": "Study test2 not found in Simulations."
}
```

### API Token is invalid

**Condition** : When the deployment has api token enabled, and the api token given is not correct.
**Code** : `401`

**Content example** :

```json
{
    "status_code": 401,
    "message": "Invalid token for deployment Simulations."
}
```

### Orphan Reward

**Condition** : There is no orphan interaction (interaction with empty reward), so the reward sent is orphan, which won't be saved into the database.
**Code** : `400`

**Content example** :

```json
{
    "status_code": 400,
    "message": "There is no interaction this reward to be appended to."
}
```

### Study has stopped

**Condition**: When the study has been stopped.
**code**: `409`

**Content example** :

```json
{
    "status_code": 409,
    "message": "Study test1 in Simulations has stopped."
}
```

## Notes

* There may be other error cases that are not implemented yet.