#!/bin/bash

echo "🚀 Deploying SpamShield API to AWS..."

# Check if we're in the right directory
if [ ! -f "api/prediction_server.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create API directory on server
echo "📁 Creating API directory..."
mkdir -p ~/spamshield-api

# Copy API files
echo "📦 Copying API files..."
cp -r api/* ~/spamshield-api/
cp -r groupme_bot ~/spamshield-api/
cp -r data ~/spamshield-api/

# Create virtual environment
echo "🐍 Setting up Python environment..."
cd ~/spamshield-api
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service file
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/spamshield-api.service > /dev/null <<EOF
[Unit]
Description=SpamShield API Server
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=/home/$USER/spamshield-api
Environment=PATH=/home/$USER/spamshield-api/venv/bin
ExecStart=/home/$USER/spamshield-api/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "🔄 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable spamshield-api
sudo systemctl start spamshield-api

# Check status
echo "📊 Checking service status..."
sudo systemctl status spamshield-api --no-pager

echo ""
echo "🎉 API deployment complete!"
echo ""
echo "📋 Service commands:"
echo "  sudo systemctl start spamshield-api    # Start service"
echo "  sudo systemctl stop spamshield-api     # Stop service"
echo "  sudo systemctl restart spamshield-api  # Restart service"
echo "  sudo systemctl status spamshield-api   # Check status"
echo "  sudo journalctl -u spamshield-api -f   # View logs"
echo ""
echo "🌐 API will be available at: http://your-server-ip:5001"
echo "🏥 Health check: http://your-server-ip:5001/api/health"
