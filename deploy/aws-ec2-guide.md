# AWS EC2 Deployment Guide

## Prerequisites
- AWS account
- EC2 instance (Ubuntu 20.04+ recommended)
- SSH key pair
- GroupMe API key

## Step 1: Launch EC2 Instance

### Instance Configuration
- **AMI**: Ubuntu Server 20.04 LTS (free tier eligible)
- **Instance Type**: t2.micro (free tier) or t3.small for production
- **Storage**: 8GB minimum (free tier)
- **Security Group**: Allow SSH (port 22) from your IP

### Launch Steps
1. Go to AWS Console → EC2 → Launch Instance
2. Choose Ubuntu Server 20.04 LTS
3. Select t2.micro (free tier)
4. Configure Security Group:
   - SSH (port 22) from your IP
   - No need for HTTP/HTTPS unless you add a web interface later
5. Create or select a key pair
6. Launch instance

## Step 2: Connect to EC2

```bash
# Connect via SSH (replace with your details)
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip.compute.amazonaws.com
```

## Step 3: Run Setup Script

```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/yourusername/GroupMe_Anti-Spam_Bot/main/deploy/ec2-setup.sh | bash
```

**Or manually:**
```bash
# Clone the repository
git clone https://github.com/yourusername/GroupMe_Anti-Spam_Bot.git
cd GroupMe_Anti-Spam_Bot

# Make setup script executable
chmod +x deploy/ec2-setup.sh
./deploy/ec2-setup.sh
```

## Step 4: Configure the Bot

```bash
# Switch to bot user
sudo su - bot

# Edit environment file
nano .env
```

**Add your credentials to .env:**
```bash
API_KEY=your_actual_groupme_api_key
BOT_USER_ID=your_bot_user_id
GROUP_ID=your_group_id
```

## Step 5: Train the Model

```bash
# Activate virtual environment
source venv/bin/activate

# Train the model
python -m groupme_bot.cli train
```

## Step 6: Configure and Start Service

```bash
# Edit service file with your group ID
sudo nano /etc/systemd/system/groupme-bot.service
```

**Replace `GROUP_ID_PLACEHOLDER` with your actual group ID**

```bash
# Enable and start the service
sudo systemctl enable groupme-bot
sudo systemctl start groupme-bot

# Check status
sudo systemctl status groupme-bot
```

## Step 7: Monitor the Bot

```bash
# View real-time logs
sudo journalctl -u groupme-bot -f

# Check recent logs
sudo journalctl -u groupme-bot --since "1 hour ago"

# Check service status
sudo systemctl status groupme-bot
```

## Step 8: Update Deployment (Optional)

Create a deployment script for easy updates:

```bash
# Edit deployment script with your EC2 details
nano deploy/ec2-deploy.sh

# Make executable
chmod +x deploy/ec2-deploy.sh

# Run deployment
./deploy/ec2-deploy.sh
```

## Troubleshooting

### Common Issues

**1. Service won't start:**
```bash
# Check logs
sudo journalctl -u groupme-bot -n 50

# Check configuration
sudo systemctl status groupme-bot
```

**2. Permission denied:**
```bash
# Fix permissions
sudo chown -R bot:bot /home/bot/groupme-bot
```

**3. Import errors:**
```bash
# Reinstall package
sudo su - bot
source venv/bin/activate
pip install -e .
```

**4. API errors:**
```bash
# Check API key
cat .env | grep API_KEY

# Test API connection
python -m groupme_bot.cli groups
```

### Useful Commands

```bash
# Restart service
sudo systemctl restart groupme-bot

# Stop service
sudo systemctl stop groupme-bot

# View all logs
sudo journalctl -u groupme-bot

# Check disk space
df -h

# Check memory usage
free -h

# Monitor system resources
htop
```

## Security Considerations

1. **Keep your API key secure** - never commit it to git
2. **Use IAM roles** instead of hardcoded AWS credentials
3. **Regular security updates** - `sudo apt update && sudo apt upgrade`
4. **Monitor logs** for suspicious activity
5. **Backup data** regularly

## Cost Optimization

- **Free tier**: t2.micro for 12 months
- **Spot instances**: 60-90% cost savings for non-critical workloads
- **Reserved instances**: 30-60% savings for long-term usage
- **Auto-scaling**: Scale down during low usage

## Monitoring and Alerts

Consider setting up:
- CloudWatch alarms for CPU/memory usage
- SNS notifications for service failures
- Log aggregation with CloudWatch Logs
- Health checks for the bot service
