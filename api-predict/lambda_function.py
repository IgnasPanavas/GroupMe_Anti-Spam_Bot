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
        print("DEBUG: load_model() called")
        # Path to model files (relative to lambda package)
        model_file = 'data/training/spam_detection_model.pkl'
        vectorizer_file = 'data/training/tfidf_vectorizer.pkl'
        
        print(f"DEBUG: Checking if model file exists: {model_file}")
        print(f"DEBUG: Checking if vectorizer file exists: {vectorizer_file}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Listing data/training directory:")
        try:
            print(f"DEBUG: {os.listdir('data/training')}")
        except Exception as e:
            print(f"DEBUG: Error listing directory: {e}")
        
        if os.path.exists(model_file) and os.path.exists(vectorizer_file):
            print("DEBUG: Both files exist, loading model...")
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            print(f"DEBUG: Model loaded successfully: {type(model)}")
            
            print("DEBUG: Loading vectorizer...")
            with open(vectorizer_file, 'rb') as f:
                vectorizer = pickle.load(f)
            print(f"DEBUG: Vectorizer loaded successfully: {type(vectorizer)}")
            
            print("DEBUG: Checking vectorizer attributes...")
            if hasattr(vectorizer, 'vocabulary_'):
                print(f"DEBUG: Vectorizer has vocabulary_ with {len(vectorizer.vocabulary_)} terms")
            else:
                print("DEBUG: Vectorizer missing vocabulary_ attribute!")
            
            if hasattr(vectorizer, 'idf_'):
                print(f"DEBUG: Vectorizer has idf_ with length {len(vectorizer.idf_)}")
            else:
                print("DEBUG: Vectorizer missing idf_ attribute!")
            
            return True
        else:
            print("DEBUG: Model files not found")
            return False
            
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"DEBUG: predict_spam called with text: {text}")
        print(f"DEBUG: Global model is None: {model is None}")
        print(f"DEBUG: Global vectorizer is None: {vectorizer is None}")
        print(f"DEBUG: Model type: {type(model)}")
        print(f"DEBUG: Vectorizer type: {type(vectorizer)}")
        
        if model is None or vectorizer is None:
            print("DEBUG: Model or vectorizer is None, returning error")
            return {"error": "Model not loaded"}
        
        # Preprocess text
        processed_text = preprocess_text(text)
        print(f"DEBUG: Processed text: {processed_text}")
        
        if not processed_text:
            return {
                "prediction": "legitimate",
                "confidence": 0.0,
                "processed_text": "",
                "message": "No text content to analyze"
            }
        
        # Transform text using vectorizer
        print("DEBUG: About to call vectorizer.transform")
        features = vectorizer.transform([processed_text])
        print(f"DEBUG: Transform successful, features shape: {features.shape}")
        
        # Make prediction
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        print(f"DEBUG: Prediction: {prediction}, Probabilities: {probabilities}")
        
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
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def lambda_handler(event, context):
    """Lambda handler focused solely on spam prediction"""
    print(f"Prediction Lambda invoked with event: {event}")
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
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/predict')
        
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
        
        # Handle prediction requests
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
        
        # Health check endpoint
        elif http_method == 'GET' and (path == '/health' or path.endswith('/health')):
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
                    'message': 'SpamShield Prediction API is running',
                    'model_loaded': model is not None,
                    'model_type': type(model).__name__ if model else None,
                    'service': 'prediction'
                })
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps({'error': 'Method not allowed', 'allowed_methods': ['POST', 'OPTIONS']})
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
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error', 
                'details': str(e),
                'traceback': traceback_str,
                'event_received': str(event)[:500] if event else 'No event received'
            })
        }