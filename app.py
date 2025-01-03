from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import docker
import os
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
client = docker.from_env()

UPLOAD_FOLDER = 'uploads'
DEPLOY_FOLDER = 'deployments'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DEPLOY_FOLDER, exist_ok=True)

deployments = {}

class LogWatcher(FileSystemEventHandler):
    def __init__(self, deployment_id):
        self.deployment_id = deployment_id
        
    def on_modified(self, event):
        if event.src_path.endswith('.log'):
            with open(event.src_path, 'r') as f:
                logs = f.read()
                socketio.emit(f'logs_{self.deployment_id}', {'logs': logs})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deploy', methods=['POST'])
def deploy():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    deployment_id = str(uuid.uuid4())
    deployment_path = os.path.join(DEPLOY_FOLDER, deployment_id)
    os.makedirs(deployment_path, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(deployment_path, file.filename)
    file.save(file_path)
    
    # Create Dockerfile for the deployment
    dockerfile_content = """
FROM python:3.9
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
"""
    
    with open(os.path.join(deployment_path, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)
    
    # Build and run the container
    try:
        image = client.images.build(path=deployment_path, tag=f'app_{deployment_id}')
        container = client.containers.run(
            f'app_{deployment_id}',
            detach=True,
            ports={'5000/tcp': None},
            name=f'app_{deployment_id}'
        )
        
        # Get the assigned port
        container_info = client.containers.get(container.id)
        port = list(container_info.ports.values())[0][0]['HostPort']
        
        # Setup log watching
        log_file = os.path.join(deployment_path, f'{deployment_id}.log')
        observer = Observer()
        observer.schedule(LogWatcher(deployment_id), deployment_path, recursive=False)
        observer.start()
        
        deployments[deployment_id] = {
            'container_id': container.id,
            'port': port,
            'status': 'running'
        }
        
        return jsonify({
            'deployment_id': deployment_id,
            'url': f'http://localhost:{port}',
            'status': 'deployed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/deployments', methods=['GET'])
def list_deployments():
    return jsonify(deployments)

@app.route('/deployment/<deployment_id>', methods=['GET'])
def get_deployment(deployment_id):
    if deployment_id not in deployments:
        return jsonify({'error': 'Deployment not found'}), 404
    return jsonify(deployments[deployment_id])

@app.route('/deployment/<deployment_id>/stop', methods=['POST'])
def stop_deployment(deployment_id):
    if deployment_id not in deployments:
        return jsonify({'error': 'Deployment not found'}), 404
    
    try:
        container = client.containers.get(deployments[deployment_id]['container_id'])
        container.stop()
        container.remove()
        deployments[deployment_id]['status'] = 'stopped'
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
