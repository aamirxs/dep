# Python Application Deployer

This is a deployment server that can handle Python/Flask applications. It provides automatic containerization and deployment of Python applications with real-time logging capabilities.

## Features

- File upload and deployment
- Docker-based containerization
- Real-time application logs
- Deployment management (start/stop)
- Unique URLs for each deployment

## Requirements

- Python 3.9+
- Docker
- Required Python packages (see requirements.txt)

## Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Make sure Docker is running on your system

3. Start the deployment server:
```bash
python app.py
```

## API Endpoints

### Deploy Application
- **POST** `/deploy`
  - Upload Python application files
  - Returns deployment ID and URL

### List Deployments
- **GET** `/deployments`
  - List all current deployments

### Get Deployment Info
- **GET** `/deployment/<deployment_id>`
  - Get information about a specific deployment

### Stop Deployment
- **POST** `/deployment/<deployment_id>/stop`
  - Stop a running deployment

## Real-time Logs

The server uses WebSocket connections to provide real-time logs for each deployment. Connect to the WebSocket endpoint and subscribe to the logs channel for your deployment ID.
