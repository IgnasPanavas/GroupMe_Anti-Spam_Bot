#!/bin/bash

# Quick Start Script for Local Development

set -e

echo "🚀 Quick Start for GroupMe Anti-Spam Bot"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API credentials!"
    echo "   nano .env"
    exit 1
fi

# Check if API_KEY is set
if ! grep -q "API_KEY=your_groupme_api_key_here" .env; then
    echo "✅ .env file looks configured"
else
    echo "⚠️  Please set your API_KEY in .env file"
    echo "   nano .env"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Train model if it doesn't exist
if [ ! -f "data/training/spam_detection_model.pkl" ]; then
    echo "🤖 Training model..."
    python -m groupme_bot.cli train
else
    echo "✅ Model already exists"
fi

echo ""
echo "🎉 Setup complete! You can now:"
echo ""
echo "📋 List your groups:"
echo "   python -m groupme_bot.cli groups"
echo ""
echo "🤖 Start the bot (replace GROUP_ID with your actual group ID):"
echo "   python -m groupme_bot.cli start --group-id GROUP_ID"
echo ""
echo "📊 Collect training data:"
echo "   python -m groupme_bot.cli collect --group-id GROUP_ID --limit 100"
echo ""
echo "🔄 Retrain model:"
echo "   python -m groupme_bot.cli train"
