
Environment:

1. Node: 18.16.0
2. Python: 3.9

  ## Install Frontend (Dev)
  ```
  cd frontend
  npm install
  npm run dev
  ```
  Now, you should be able to access the frontend at localhost: http://localhost:3000
  If you have pm2 installed, you can run the frontend in backend by `pm2 start "npm run start" --name mooclet_dashboard` for production, but make sure you run `npm run build` first.

  ## Install Backend (Dev)
Go into the backend folder by running: `cd backend`
You need to fill in environment variables. First, you need to make a `.env` file by copying `.env-sample`: 
```
cp .env-sample .env
```
Fill in/Modify the following information:
```
MONGO_DB_CONNECTION_STRING=
PSQL_HOST=
PSQL_PASSWORD=
PSQL_DATABASE=moocletengine
PSQL_USER=moocletengine
PSQL_PORT=5432
MOOCLET_TOKEN=
MOOCLET_ENGINE_URL=
```

The Backend is in Python. So there are some Python libraries need to be installed (as specified in requirements.txt):
```
pip install -r requirements.txt
```
Now, you can start the backend by running `python3 engine.py`

Notes:

The backend is running at port 20110 by default. If you need to run backend at a different port, you need to change the frontend setting to let the APIs calls be rewritten to the right port. You can do it by editing the following code block in `next.config.js`: 
```
const  API_URL  =  'http://127.0.0.1:20110';
```