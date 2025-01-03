#!/bin/bash

# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-venv python3-pip nginx docker.io

# Create directory for the application
sudo mkdir -p /opt/deployer
sudo chown $USER:$USER /opt/deployer

# Copy application files
cp -r * /opt/deployer/

# Create virtual environment
cd /opt/deployer
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn eventlet

# Setup logs directory
sudo mkdir -p /var/log/gunicorn
sudo chown $USER:$USER /var/log/gunicorn

# Setup systemd service
sudo cp deployer.service /etc/systemd/system/
sudo sed -i "s/ubuntu/$USER/g" /etc/systemd/system/deployer.service
sudo sed -i "s|/path/to/deployer|/opt/deployer|g" /etc/systemd/system/deployer.service

# Setup Nginx
sudo cp nginx_config /etc/nginx/sites-available/deployer
sudo ln -s /etc/nginx/sites-available/deployer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl daemon-reload
sudo systemctl enable deployer
sudo systemctl start deployer
sudo systemctl restart nginx

# Setup Docker permissions
sudo usermod -aG docker $USER

echo "Installation complete! Please update the domain in /etc/nginx/sites-available/deployer"
echo "Then restart Nginx with: sudo systemctl restart nginx"
