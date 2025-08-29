#!/bin/bash

# EC2 Setup Script for GroupMe Anti-Spam Bot
# Run this on a fresh Ubuntu/Debian EC2 instance

set -e  # Exit on any error

echo "🚀 Setting up GroupMe Anti-Spam Bot on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv git curl wget

# Install additional system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y build-essential python3-dev

# Create bot user
echo "👤 Creating bot user..."
sudo useradd -m -s /bin/bash bot
sudo usermod -aG sudo bot

# Switch to bot user
echo "🔄 Switching to bot user..."
sudo -u bot bash << 'EOF'

# Create bot directory
mkdir -p ~/groupme-bot
cd ~/groupme-bot

# Clone repository (replace with your actual repo URL)
git clone https://github.com/yourusername/GroupMe_Anti-Spam_Bot.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Create data directories
mkdir -p data/logs data/training data/config

# Set up environment file
cp env.example .env
echo "⚠️  Please edit .env file with your API credentials!"

# Create systemd service file
sudo tee /etc/systemd/system/groupme-bot.service > /dev/null << 'SERVICEFILE'
[Unit]
Description=GroupMe Anti-Spam Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/home/bot/groupme-bot
Environment=PATH=/home/bot/groupme-bot/venv/bin
ExecStart=/home/bot/groupme-bot/venv/bin/python -m groupme_bot.cli start --group-id GROUP_ID_PLACEHOLDER
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEFILE

# Reload systemd
sudo systemctl daemon-reload

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your API credentials:"
echo "   nano .env"
echo ""
echo "2. Update the service file with your group ID:"
echo "   sudo nano /etc/systemd/system/groupme-bot.service"
echo "   (Replace GROUP_ID_PLACEHOLDER with your actual group ID)"
echo ""
echo "3. Train the model:"
echo "   source venv/bin/activate"
echo "   python -m groupme_bot.cli train"
echo ""
echo "4. Start the service:"
echo "   sudo systemctl enable groupme-bot"
echo "   sudo systemctl start groupme-bot"
echo ""
echo "5. Check status:"
echo "   sudo systemctl status groupme-bot"
echo "   sudo journalctl -u groupme-bot -f"

EOF
