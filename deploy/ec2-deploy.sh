#!/bin/bash

# EC2 Deployment Script
# Run this to deploy updates to an existing EC2 instance

set -e

echo "🚀 Deploying GroupMe Anti-Spam Bot to EC2..."

# Configuration
EC2_USER="ubuntu"  # or "ec2-user" for Amazon Linux
EC2_HOST="your-ec2-ip-or-domain.com"
SSH_KEY="~/.ssh/your-key.pem"

# Stop the service
echo "⏹️  Stopping bot service..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "sudo systemctl stop groupme-bot"

# Pull latest code
echo "📥 Pulling latest code..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd ~/groupme-bot && git pull origin main"

# Update dependencies
echo "📦 Updating dependencies..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd ~/groupme-bot && source venv/bin/activate && pip install -r requirements.txt && pip install -e ."

# Train model (optional - uncomment if needed)
# echo "🤖 Training model..."
# ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd ~/groupme-bot && source venv/bin/activate && python -m groupme_bot.cli train"

# Start the service
echo "▶️  Starting bot service..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "sudo systemctl start groupme-bot"

# Check status
echo "📊 Checking service status..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "sudo systemctl status groupme-bot"

echo "✅ Deployment complete!"
echo ""
echo "📝 Useful commands:"
echo "  View logs: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo journalctl -u groupme-bot -f'"
echo "  Restart: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo systemctl restart groupme-bot'"
echo "  Stop: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'sudo systemctl stop groupme-bot'"
