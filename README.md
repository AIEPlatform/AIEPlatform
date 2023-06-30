
  

## Requirements:
1. Node: 18.16.0
2. Python: 3.9
3. MongoDB 6.0 with Replication (a local Database is optional, you can use a remote MongoDB server, for example, MongoDB Atlas)
4. OpenAI API Key (Optional)
5. Gmail Credentials for sending notification emails (Optional)

## Environment File
You need to fill in environment variables. First, you need to make a `config.sample.py` file by copying `config.py`:

```
cp config.sample.py config.py
```

Fill in `config.py` file.

## Development

### Frontend Installation
```
cd frontend
npm install
npm run dev
```
Now, you should be able to access the frontend at localhost: http://localhost:3000

### Backend Installation
Go into the backend folder by running: `cd backend`

The Backend is in Python. So there are some Python libraries need to be installed (as specified in requirements.txt):

```
pip install -r requirements.txt
```
Now, you can start the backend by running `python3 dataarrow.py`

Notes:

The backend is running at port 20110 by default. If you need to run backend at a different port, you need to change the frontend setting to let the APIs calls be rewritten to the right port. You can do it by editing the following code block in `next.config.js`:

```
const API_URL = 'http://127.0.0.1:20110';
```
## Production
Make sure that you have `pm2` installed.
Run `./production.sh`.

## Instructions on installing external software

### Install MongoDB and Set up Replication 
#### Installation (Use Ubuntu 22.04 LTS as an example)
Reference: [Install MongoDB Community Edition on Ubuntu — MongoDB Manual](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/)

Note that MongoDB is not compatible with Windows WSL.
```
sudo apt-get install gnupg

sudo apt install curl

curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

sudo apt-get update

sudo apt-get install -y mongodb-org

```

You can start the MongoDB software by `sudo systemctl start mongod`.
You can start the MongoDB on system boot by `sudo systemctl enable mongod`.
You can check the MongoDB status by `sudo systemctl status mongod`.

#### Create User for DataArrow
When you make sure that MongoDB is running, type `mongosh`.
Switch to the admin collection by `use admin`;

Let's create an admin user first before we turn on authedication.
`db.createUser({user: "admin", "pwd": passwordPrompt(), roles: ["root"]});`

Give a secure password.

Now, let's create the user for our DB.
`db.createUser({user: "dataarrow", "pwd": passwordPrompt(), roles: [{ role: 'readWrite', db: 'dataarrow' }]});`

Type `ctrl+c` to exit the mongosh.

Modify MongoDB configuration file at `/etc/mongod.conf`:

Uncomment the `security` section, add/replace with the following information:
```
security:
    authorization: "enabled"
```

** keyFile is required for our next step: replication set.

Restart MongoDB by `sudo systemctl restart mongod`

Now, the authedication is on. We can move on to enable replication set.

#### Set up Replication Set
Reference: [MongoDB Replica Set Configuration: 7 Easy Steps - Learn | Hevo (hevodata.com)](https://hevodata.com/learn/mongodb-replica-set-config/)

Use a `root` by `sudo su`.
Generate key (which's required for replication set).
```
mkdir -p /etc/mongodb/keys/
openssl rand -base64 756 > /etc/mongodb/keys/mongo-key
chmod 400 /etc/mongodb/keys/mongo-key
chown -R mongodb:mongodb /etc/mongodb
```
*** You can also choose to generate the key somewhere else. But make sure that mongodb can access it.

Modify MongoDB configuration file at `/etc/mongod.conf`:

Uncomment the `replication` section, add/replace with the following information:

```
security:
    authorization: "enabled"
    keyFile: /etc/mongodb/keys/mongo-key
replication:
	replSetName: "replicaset-01"
```

Be careful about the intent.

Restart MongoDB by `sudo systemctl restart mongod`

Enter MongoDB shell by `mongosh`. Switch to admin by `use admin`;

Auth yourself with the admin account by: `db.auth(username, password)`;

Initialize the replication set: `rs.initiate()`.

Now, we can get access to the replication set by `mongodb://username:password@localhost:27017/?authMechanism=DEFAULT&replicaSet=replicaset-01`.


### Install NodeJS in Ubuntu 22.04LTS via NVM

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash

source ~/.bashrc

nvm install 18
```

## Supplementary readings
1. To install Node & NPM in MacOS, follow this article: [How To Install NVM on macOS with Homebrew – TecAdmin](https://tecadmin.net/install-nvm-macos-with-homebrew/)
2. To install pm2: [pm2 - npm (npmjs.com)](https://www.npmjs.com/package/pm2)
3. [Install MongoDB Community Edition on Ubuntu — MongoDB Manual](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/)
4. [MongoDB Replica Set Configuration: 7 Easy Steps - Learn | Hevo (hevodata.com)](https://hevodata.com/learn/mongodb-replica-set-config/)
5. [How to Create User & add Role in MongoDB (guru99.com)](https://www.guru99.com/mongodb-create-user.html)