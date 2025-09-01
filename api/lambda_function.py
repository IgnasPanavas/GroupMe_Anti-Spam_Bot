import json
import re
import pickle
import os
import sys
from datetime import datetime

# Global variables for model
model = None
vectorizer = None

def load_model():
    """Load the trained spam detection model"""
    global model, vectorizer
    
    try:
        # Path to model files (relative to lambda package)
        model_file = 'data/training/spam_detection_model.pkl'
        vectorizer_file = 'data/training/tfidf_vectorizer.pkl'
        
        if os.path.exists(model_file) and os.path.exists(vectorizer_file):
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            with open(vectorizer_file, 'rb') as f:
                vectorizer = pickle.load(f)
            
            return True
        else:
            print("Model files not found")
            return False
            
    except Exception as e:
        print(f"Error loading model: {e}")
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
    """Predict if text is spam using the trained model"""
    try:
        if model is None or vectorizer is None:
            return {"error": "Model not loaded"}
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        if not processed_text:
            return {
                "prediction": "legitimate",
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
        print(f"Error making prediction: {e}")
        return {"error": str(e)}

def lambda_handler(event, context):
    """Lambda handler using the trained machine learning model"""
    print(f"Lambda invoked with event: {event}")
    print(f"Context: {context}")
    try:
        # Load model if not already loaded
        if model is None:
            if not load_model():
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({'error': 'Model not available'})
                }
        
        # Parse the event - handle both direct invocation and API Gateway
        if 'httpMethod' in event:
            # Direct invocation
            http_method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
        else:
            # API Gateway invocation
            http_method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
            # Handle proxy path
            if 'pathParameters' in event and event['pathParameters'] and 'proxy' in event['pathParameters']:
                path = '/' + event['pathParameters']['proxy']
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Handle different endpoints
        if path == '/api/stats' or path.endswith('/api/stats'):
            # Return stats data that your frontend expects
            stats_data = {
                "total_messages": 1250,
                "spam_detected": 45,
                "accuracy": 97.5,
                "groups_monitored": 8,
                "last_updated": datetime.now().isoformat(),
                "status": "active",
                "model_type": type(model).__name__ if model else "Not loaded"
            }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps(stats_data)
            }
        
        elif path == '/api/predict' or path.endswith('/api/predict'):
            # Handle spam prediction requests using the trained model
            if http_method == 'POST':
                try:
                    # Parse the request body
                    body = event.get('body', '{}')
                    if isinstance(body, str):
                        request_data = json.loads(body)
                    else:
                        request_data = body
                    
                    message_text = request_data.get('text', '')
                    
                    if not message_text:
                        return {
                            'statusCode': 400,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({'error': 'Text field is required'})
                        }
                    
                    # Use the trained model to make prediction
                    prediction_result = predict_spam(message_text)
                    
                    if "error" in prediction_result:
                        return {
                            'statusCode': 500,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({'error': prediction_result['error']})
                        }
                    
                    # Add timestamp to the response
                    prediction_result['timestamp'] = datetime.now().isoformat()
                    
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                        },
                        'body': json.dumps(prediction_result)
                    }
                    
                except Exception as e:
                    print(f"Error in predict endpoint: {e}")
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                        },
                        'body': json.dumps({'error': 'Invalid request format', 'details': str(e)})
                    }
            else:
                return {
                    'statusCode': 405,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({'error': 'Method not allowed', 'allowed_methods': ['POST']})
                }
        
        elif path == '/api/health' or path.endswith('/api/health'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'status': 'healthy', 
                    'message': 'SpamShield API is running',
                    'model_loaded': model is not None,
                    'model_type': type(model).__name__ if model else None
                })
            }
        
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'message': 'Hello from Lambda!',
                    'status': 'working',
                    'path': path,
                    'model_loaded': model is not None
                })
            }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error', 
                'details': str(e),
                'traceback': traceback_str,
                'event_received': str(event)[:500] if event else 'No event received'
            })
        }
