#!/bin/bash

# SpamShield Platform Startup Script

set -e

echo "🚀 Starting SpamShield Platform..."

# Check if .env file exists
if [ ! -f "spamshield_platform/.env" ]; then
    echo "⚠️  No .env file found. Copying from example..."
    cp spamshield_platform/config.env.example spamshield_platform/.env
    echo "📝 Please edit spamshield_platform/.env with your configuration before running again."
    exit 1
fi

# Load environment variables
if [ -f "spamshield_platform/.env" ]; then
    export $(cat spamshield_platform/.env | grep -v '^#' | xargs)
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p spamshield_platform/logs
mkdir -p data/training

# Check if database is accessible
echo "🔍 Checking database connection..."
if command -v psql &> /dev/null; then
    if psql $DATABASE_URL -c "SELECT 1;" &> /dev/null; then
        echo "✅ Database connection successful"
    else
        echo "❌ Database connection failed. Please check your DATABASE_URL."
        echo "Current DATABASE_URL: $DATABASE_URL"
        exit 1
    fi
else
    echo "⚠️  psql not found. Skipping database check."
fi

# Check if required model files exist
if [ ! -f "data/training/spam_detection_model.pkl" ] || [ ! -f "data/training/tfidf_vectorizer.pkl" ]; then
    echo "⚠️  ML model files not found in data/training/"
    echo "Please ensure you have:"
    echo "  - data/training/spam_detection_model.pkl"
    echo "  - data/training/tfidf_vectorizer.pkl"
    echo ""
    echo "You can train a model using: python retrain_model.py"
    exit 1
fi

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -r spamshield_platform/requirements.txt

# Run database migrations (if needed)
echo "🗄️  Running database setup..."
python -c "
from spamshield_platform.database.connection import init_database
try:
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

# Start the platform
echo "🎯 Starting SpamShield Platform..."
echo "API will be available at: http://$HOST:$PORT"
echo "Health check: http://$HOST:$PORT/health"
echo "API docs: http://$HOST:$PORT/docs"
echo ""

# Run with proper Python path
PYTHONPATH=. python spamshield_platform/main.py
