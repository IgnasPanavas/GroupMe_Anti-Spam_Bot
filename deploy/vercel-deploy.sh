#!/bin/bash

echo "🚀 Deploying SpamShield to Vercel..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the spamshield-frontend directory"
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📥 Installing Vercel CLI..."
    npm install -g vercel
fi

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Go to your Vercel dashboard"
    echo "2. Navigate to Domains settings"
    echo "3. Add custom domain: spamshield.ignaspanavas.com"
    echo "4. Update DNS records at your domain registrar"
    echo ""
    echo "🔗 Your site is now live!"
else
    echo "❌ Deployment failed"
    exit 1
fi
