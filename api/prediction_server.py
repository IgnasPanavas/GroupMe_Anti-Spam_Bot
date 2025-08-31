#!/usr/bin/env python3
"""
SpamShield Prediction API Server
Provides REST API endpoints for spam prediction and bot management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import os
import sys
import re
from datetime import datetime
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot components
from groupme_bot.utils.api_client import create_api_client
from groupme_bot.utils.config import ConfigManager

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model
model = None
vectorizer = None
config_manager = None
api_client = None

def load_model():
    """Load the trained spam detection model"""
    global model, vectorizer
    
    try:
        model_file = 'data/training/spam_detection_model.pkl'
        vectorizer_file = 'data/training/tfidf_vectorizer.pkl'
        
        if os.path.exists(model_file) and os.path.exists(vectorizer_file):
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            with open(vectorizer_file, 'rb') as f:
                vectorizer = pickle.load(f)
            
            logger.info(f"Model loaded successfully: {type(model).__name__}")
            return True
        else:
            logger.error("Model files not found")
            return False
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def preprocess_text(text):
    """Preprocess text for prediction"""
    if not text or text == '':
        return ''
    
    # Convert to lowercase
    text = str(text).lower()
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def predict_spam(text):
    """Predict if text is spam"""
    try:
        if model is None or vectorizer is None:
            return {"error": "Model not loaded"}
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        if not processed_text:
            return {
                "prediction": "regular",
                "confidence": 0.0,
                "processed_text": "",
                "message": "No text content to analyze"
            }
        
        # Transform text using vectorizer
        features = vectorizer.transform([processed_text])
        
        # Make prediction
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        
        # Get confidence for the predicted class
        if prediction == 'spam':
            confidence = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        else:
            confidence = probabilities[0]
        
        return {
            "prediction": prediction,
            "confidence": float(confidence),
            "confidence_percentage": f"{confidence * 100:.1f}%",
            "processed_text": processed_text,
            "message": f"Predicted as {prediction} with {confidence * 100:.1f}% confidence"
        }
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        return {"error": str(e)}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SpamShield Prediction API",
        "model_loaded": model is not None
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict if a message is spam"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Text field is required"}), 400
        
        text = data['text']
        result = predict_spam(text)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in predict endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get bot statistics"""
    try:
        # Mock stats for now - in production, you'd get these from a database
        stats = {
            "messages_protected": 1247,
            "spam_blocked": 89,
            "groups_protected": 3,
            "accuracy": "97.5%",
            "model_type": type(model).__name__ if model else "Not loaded",
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Get protected groups"""
    try:
        if api_client is None:
            return jsonify({"error": "API client not initialized"}), 500
        
        groups = api_client.get_groups()
        
        # Filter to only show groups where bot is active
        active_groups = []
        for group in groups:
            active_groups.append({
                "id": group.get('group_id'),
                "name": group.get('name'),
                "members": group.get('members_count'),
                "status": "active"  # You could check actual status here
            })
        
        return jsonify(active_groups)
        
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/activity', methods=['GET'])
def get_activity():
    """Get recent activity"""
    try:
        # Mock activity data - in production, you'd get this from logs/database
        activity = [
            {
                "type": "spam_blocked",
                "group": "UGA Shitposting",
                "message": "Spam blocked in \"UGA Shitposting\"",
                "timestamp": datetime.now().isoformat(),
                "confidence": "95.2%"
            },
            {
                "type": "bot_activated",
                "group": "Anti-spam-bot-test-group",
                "message": "SpamShield activated in \"Anti-spam-bot-test-group\"",
                "timestamp": datetime.now().isoformat(),
                "confidence": None
            }
        ]
        
        return jsonify(activity)
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Handle bot settings"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            # In production, you'd save this to a database
            logger.info(f"Settings updated: {data}")
            return jsonify({"status": "success", "message": "Settings updated"})
        
        # Return current settings
        current_settings = {
            "check_interval": 15,
            "confidence_threshold": 0.8,
            "enable_notifications": True,
            "model_file": "data/training/spam_detection_model.pkl"
        }
        
        return jsonify(current_settings)
        
    except Exception as e:
        logger.error(f"Error handling settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_predictions():
    """Test endpoint with sample predictions"""
    test_messages = [
        "selling concert tickets dm me",
        "Hello, how are you doing today?",
        "selling parking permit text 404-555-1234",
        "This is a legitimate message about our meeting tomorrow",
        "selling football tickets very urgent 2039095465"
    ]
    
    results = []
    for message in test_messages:
        result = predict_spam(message)
        results.append({
            "message": message,
            "prediction": result
        })
    
    return jsonify(results)

if __name__ == '__main__':
    print("🛡️ Starting SpamShield Prediction API...")
    
    # Load model
    if load_model():
        print("✅ Model loaded successfully")
    else:
        print("❌ Failed to load model")
    
    # Initialize API client and config manager
    try:
        config_manager = ConfigManager()
        api_client = create_api_client()
        print("✅ API client initialized")
    except Exception as e:
        print(f"⚠️ API client initialization failed: {e}")
    
    print("📡 API will be available at: http://localhost:5001")
    print("🏥 Health check: http://localhost:5001/api/health")
    print("🧪 Test predictions: http://localhost:5001/api/test")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
