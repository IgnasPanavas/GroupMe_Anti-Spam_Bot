#!/bin/bash

echo "🌐 Setting up Nginx reverse proxy for SpamShield API..."

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create Nginx configuration
echo "⚙️ Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/spamshield-api > /dev/null <<EOF
server {
    listen 80;
    server_name api.spamshield.ignaspanavas.com;  # Change this to your domain

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
        
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
}
EOF

# Enable the site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/spamshield-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    
    # Restart Nginx
    echo "🔄 Restarting Nginx..."
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    echo ""
    echo "🎉 Nginx setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your domain DNS to point to this server"
    echo "2. Update the frontend API URL to: http://api.spamshield.ignaspanavas.com"
    echo "3. Test the API: curl http://api.spamshield.ignaspanavas.com/api/health"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi
