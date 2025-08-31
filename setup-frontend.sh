#!/bin/bash

echo "🛡️ Setting up SpamShield Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js and npm found"

# Navigate to frontend directory
cd spamshield-frontend

# Install dependencies
echo "📦 Installing React dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully"
else
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Install additional dependencies for the API
echo "📦 Installing API dependencies..."
cd ..
pip install flask flask-cors

if [ $? -eq 0 ]; then
    echo "✅ API dependencies installed successfully"
else
    echo "❌ Failed to install API dependencies"
    exit 1
fi

echo ""
echo "🎉 SpamShield Frontend setup complete!"
echo ""
echo "🚀 To run the application:"
echo "   1. Start the API server:"
echo "      python api/prediction_server.py"
echo ""
echo "   2. In another terminal, start the React app:"
echo "      cd spamshield-frontend"
echo "      npm start"
echo ""
echo "📱 The frontend will be available at: http://localhost:3000"
echo "🔌 The API will be available at: http://localhost:5001"
echo ""
echo "🧪 Test the prediction API:"
echo "   curl -X POST http://localhost:5001/api/predict \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"selling concert tickets dm me\"}'"
