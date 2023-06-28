#!/bin/bash

# Define the name of the task you want to check
frontend_task="DataArrow-Frontend"

# Check if the task is in the list using PM2 list command
pm2_list_output=$(pm2 list)

# Search for the task name in the PM2 list output
if [[ $pm2_list_output == *"$frontend_task"* ]]; then
  echo "Task $frontend_task is running in PM2, we need to delete it first."
  pm2 delete $frontend_task > /dev/null 2>&1
else
  echo "Task $frontend_task is not running in PM2."
fi

backend_task="DataArrow-Backend"

# Check if the task is in the list using PM2 list command
pm2_list_output=$(pm2 list)

# Search for the task name in the PM2 list output
if [[ $pm2_list_output == *"$backend_task"* ]]; then
  echo "Task $backend_task is running in PM2, we need to delete it first."
  pm2 delete $backend_task > /dev/null 2>&1
else
  echo "Task $backend_task is not running in PM2."
fi

# start frontend
cd frontend
npm install
npm run build
pm2 start npm --name $frontend_task -- start

cd ../backend
pip install -r requirements.txt
pm2 start dataarrow.py --name $backend_task

pm2 save