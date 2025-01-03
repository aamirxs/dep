document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const deployments = new Map();

    // Handle file upload
    const uploadForm = document.getElementById('uploadForm');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleUpload(e.target.files[0]);
        }
    });

    function handleUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.textContent = 'Uploading...';
        uploadStatus.className = '';

        fetch('/deploy', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            uploadStatus.textContent = 'Deployment successful!';
            uploadStatus.className = 'success';
            loadDeployments();
        })
        .catch(error => {
            uploadStatus.textContent = `Error: ${error.message}`;
            uploadStatus.className = 'error';
        });
    }

    // Load and display deployments
    function loadDeployments() {
        fetch('/deployments')
            .then(response => response.json())
            .then(data => {
                const deploymentsGrid = document.getElementById('deploymentsGrid');
                deploymentsGrid.innerHTML = '';

                Object.entries(data).forEach(([id, deployment]) => {
                    const card = createDeploymentCard(id, deployment);
                    deploymentsGrid.appendChild(card);
                    
                    // Setup WebSocket connection for logs
                    if (!deployments.has(id)) {
                        deployments.set(id, true);
                        socket.on(`logs_${id}`, (data) => {
                            const logsElement = document.getElementById(`logs_${id}`);
                            if (logsElement) {
                                logsElement.textContent = data.logs;
                                logsElement.scrollTop = logsElement.scrollHeight;
                            }
                        });
                    }
                });
            });
    }

    function createDeploymentCard(id, deployment) {
        const card = document.createElement('div');
        card.className = 'deployment-card';
        
        const statusClass = deployment.status === 'running' ? 'status-running' : 'status-stopped';
        
        card.innerHTML = `
            <h3>Deployment ${id.slice(0, 8)}</h3>
            <p>
                <span class="status ${statusClass}">${deployment.status}</span>
            </p>
            <p>Port: ${deployment.port}</p>
            <p>
                <a href="http://localhost:${deployment.port}" target="_blank" class="btn btn-primary">View App</a>
                <button onclick="stopDeployment('${id}')" class="btn btn-danger">Stop</button>
            </p>
            <div class="logs-container" id="logs_${id}"></div>
        `;
        
        return card;
    }

    // Initialize
    loadDeployments();
    setInterval(loadDeployments, 5000); // Refresh every 5 seconds
});

function stopDeployment(id) {
    fetch(`/deployment/${id}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        alert(`Error: ${error.message}`);
    });
}
