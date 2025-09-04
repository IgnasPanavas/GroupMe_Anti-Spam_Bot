#!/bin/bash

# Build script for scikit-learn Lambda package
# Based on https://serverlesscode.com/post/scikitlearn-with-amazon-linux-container/

set -e

echo "🚀 Building scikit-learn for AWS Lambda..."

# Install required packages
yum update -y
yum install -y python3 python3-pip python3-devel gcc gcc-c++ make

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install scikit-learn and dependencies with no-binary to force compilation
echo "📦 Installing numpy..."
pip install --no-binary numpy numpy

echo "📦 Installing scipy..."
pip install --no-binary scipy scipy

echo "📦 Installing scikit-learn..."
pip install --no-binary scikit-learn scikit-learn

# Create the deployment package
echo "📦 Creating deployment package..."
cd venv/lib/python3.9/site-packages
zip -r9 ../../../../lambda-package.zip .

# Go back to project root
cd ../../../..

# Add our lambda function and model files
echo "📦 Adding lambda function and model files..."
zip -g lambda-package.zip lambda_function.py
zip -g lambda-package.zip -r data/

echo "✅ Build complete! Created lambda-package.zip"
echo "📊 Package size: $(du -h lambda-package.zip | cut -f1)"
