
# Give a variable value

A user gives a variable value

**URL** : `/apis/variable/`

**Method** : `POST`

**Auth required** : OPTIONAL

**Required Request Body**

```json
{
    "deployment": "Name of the deployment",
    "study": "Name of the study",
    "user": "Name of the user",
    "variable": "Name of the variable"
    "value": "Value of the variable of the user"
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
	"where": "Specify where the variable is collected",
	"otherInformation": "JSON OBJECT that contains other information (NOT IN USE)"
}
```



## Success Responses

**Condition** : The deployment and study exists, and api token is given correctly when required.

**Code** : `200 OK`

**Content example** : 

```json
{
    "status_code": 200,
    "message": "Variable value is saved."
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

### Variable Not In Study

**Condition** : The study doesn't use the variable.
**Code** : `400`

**Content example** :

```json
{
    "status_code": 400,
    "message": "Variable sex is not in study test1 in deployment Simulations."
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

* There may be other error cases that are not implemented yet. For example, we need to check if the value is valid by checking the Variable Definition.