
# Get a treatment

Get a treatment (arm) from a study for a user.

**URL** : `/apis/treatment/`

**Method** : `POST`

**Auth required** : OPTIONAL

**Required Request Body**

```json
{
    "deployment": "Name of the deployment",
    "study": "Name of the study",
    "user": "Name of the user"
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
	"where": "Distinguish the interaction from interactions occured whereelse",
	"otherInformation": "JSON OBJECT that contains other information"
}
```



## Success Responses

**Condition** : The deployment and study exists, and api token is given correctly when required.

**Code** : `200 OK`

**Content example** : Response will include the treatment assigned.

```json
{
    "status_code": 200,
    "message": "This is your treatment.",
    "treatment": {
        "name": "version2",
        "content": "This is version 2.",
        "versionJSON": {
            "factor1": 1
        }
    }
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

## Notes

* This API doesn't necessary create an Interaction record, if, for example, the assigner doesn't allow assign a treatment before a reward is received.