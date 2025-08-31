#!/bin/bash

echo "🚀 Building and Deploying SpamShield..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the spamshield-frontend directory"
    exit 1
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build node_modules package-lock.json

# Install dependencies with legacy peer deps
echo "📦 Installing dependencies..."
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Build the app
echo "🔨 Building React app..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful!"

# Check if build directory exists
if [ ! -d "build" ]; then
    echo "❌ Build directory not found"
    exit 1
fi

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "📁 Build files are in the 'build' directory"
echo ""
echo "🌐 Deployment options:"
echo "1. Netlify: Drag the 'build' folder to netlify.com"
echo "2. Vercel: Push to GitHub and connect to Vercel"
echo "3. AWS S3: Use the AWS deployment script"
echo ""
echo "📋 Next steps:"
echo "- Upload the 'build' folder to your hosting platform"
echo "- Set up custom domain: spamshield.ignaspanavas.com"
echo "- Update DNS records at your domain registrar"
