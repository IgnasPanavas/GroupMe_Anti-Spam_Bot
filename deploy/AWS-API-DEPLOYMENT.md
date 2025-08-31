# AWS API Deployment Guide

## 🚀 **Deploy SpamShield API to AWS Server**

### **Prerequisites**
- AWS EC2 instance running Ubuntu/Debian
- SSH access to your server
- Domain name (optional, for custom domain)

---

## 📋 **Step-by-Step Deployment**

### **Step 1: Connect to Your AWS Server**
```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

### **Step 2: Clone Your Repository**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Git if not installed
sudo apt install -y git

# Clone your repository
git clone https://github.com/IgnasPanavas/GroupMe_Anti-Spam_Bot.git
cd GroupMe_Anti-Spam_Bot
```

### **Step 3: Deploy the API**
```bash
# Run the deployment script
./deploy/api-deploy.sh
```

This script will:
- ✅ Create API directory structure
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Create systemd service
- ✅ Start the API server

### **Step 4: Set Up Nginx (Optional but Recommended)**
```bash
# Run Nginx configuration script
./deploy/nginx-config.sh
```

This will:
- ✅ Install and configure Nginx
- ✅ Set up reverse proxy
- ✅ Enable CORS headers
- ✅ Configure domain routing

---

## 🔧 **Service Management**

### **Check API Status**
```bash
sudo systemctl status spamshield-api
```

### **Start/Stop/Restart API**
```bash
sudo systemctl start spamshield-api    # Start
sudo systemctl stop spamshield-api     # Stop
sudo systemctl restart spamshield-api  # Restart
```

### **View API Logs**
```bash
# View real-time logs
sudo journalctl -u spamshield-api -f

# View recent logs
sudo journalctl -u spamshield-api -n 50
```

### **Check Nginx Status**
```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

---

## 🌐 **Accessing Your API**

### **Direct Access (Port 5001)**
```
http://your-server-ip:5001/api/health
```

### **Through Nginx (Port 80)**
```
http://your-server-ip/api/health
```

### **With Custom Domain**
```
http://api.spamshield.ignaspanavas.com/api/health
```

---

## 🔒 **Security Configuration**

### **Firewall Setup**
```bash
# Allow SSH, HTTP, and API ports
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5001
sudo ufw enable
```

### **SSL Certificate (Optional)**
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d api.spamshield.ignaspanavas.com
```

---

## 📊 **Monitoring and Maintenance**

### **Check API Health**
```bash
curl http://localhost:5001/api/health
```

### **Monitor Resource Usage**
```bash
# Check CPU and memory
htop

# Check disk space
df -h

# Check running processes
ps aux | grep spamshield
```

### **Update API**
```bash
# Pull latest changes
cd ~/GroupMe_Anti-Spam_Bot
git pull

# Redeploy
./deploy/api-deploy.sh
```

---

## 🚨 **Troubleshooting**

### **API Won't Start**
```bash
# Check service status
sudo systemctl status spamshield-api

# Check logs
sudo journalctl -u spamshield-api -n 50

# Check if port is in use
sudo netstat -tlnp | grep 5001
```

### **Nginx Issues**
```bash
# Test configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### **Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER ~/spamshield-api
chmod +x ~/spamshield-api/venv/bin/*
```

---

## 🔄 **Automatic Restarts**

The API is configured with **systemd** which means:

✅ **Automatic restart** if the process crashes
✅ **Starts on boot** when server reboots
✅ **Keeps running** after you disconnect SSH
✅ **Logs all activity** for debugging

### **Why It Keeps Running After Disconnect**

1. **systemd Service**: Runs as a system service, not tied to your SSH session
2. **Background Process**: Runs independently of your terminal
3. **Auto-restart**: Automatically restarts if it crashes
4. **Boot Persistence**: Starts automatically when server boots

---

## 🌐 **Connect Frontend to API**

### **Update Frontend API URL**

In your Vercel frontend, update the API URL:

1. **Go to Vercel dashboard**
2. **Project Settings** → **Environment Variables**
3. **Add variable:**
   ```
   REACT_APP_API_URL=http://api.spamshield.ignaspanavas.com
   ```
4. **Redeploy your frontend**

### **Test the Connection**

Visit your frontend and try the prediction feature - it should now connect to your AWS API!

---

## 📞 **Support**

If you encounter issues:
1. Check the logs: `sudo journalctl -u spamshield-api -f`
2. Verify the service is running: `sudo systemctl status spamshield-api`
3. Test the API directly: `curl http://localhost:5001/api/health`
4. Check firewall settings: `sudo ufw status`
