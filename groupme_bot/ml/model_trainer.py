import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def preprocess_text(text):
    """
    Preprocess text for ML training
    """
    if pd.isna(text) or text == '':
        return ''
    
    # Convert to lowercase
    text = str(text).lower()
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def load_and_prepare_data(regular_csv='data/training/master_training_data.csv', spam_csv='data/training/augmented_spam_data.csv'):
    """
    Load and prepare the training data from both regular and spam CSV files
    """
    print("Loading training data...")
    
    dfs = []
    
    # Load regular messages from multiple sources
    regular_sources = [
        'data/training/master_training_data.csv',
        'data/training/master_training_data_backup_20250825_201229.csv'
    ]
    
    for regular_file in regular_sources:
        try:
            regular_df = pd.read_csv(regular_file)
            # Filter to only include regular messages
            regular_df = regular_df[regular_df['label'] == 'regular']
            print(f"Loaded {len(regular_df)} regular messages from {regular_file}")
            dfs.append(regular_df)
        except FileNotFoundError:
            print(f"Warning: {regular_file} not found. Skipping.")
        except Exception as e:
            print(f"Error loading {regular_file}: {e}")
    
    # Load spam messages
    try:
        spam_df = pd.read_csv(spam_csv)
        print(f"Loaded {len(spam_df)} spam messages from {spam_csv}")
        dfs.append(spam_df)
    except FileNotFoundError:
        print(f"Warning: {spam_csv} not found. Skipping spam messages.")
    except Exception as e:
        print(f"Error loading {spam_csv}: {e}")
    
    if not dfs:
        print("Error: No CSV files found. Please run the data collection first.")
        return None
    
    # Combine all dataframes
    df = pd.concat(dfs, ignore_index=True)
    print(f"Combined dataset: {len(df)} total messages")
    
    # Check for missing data
    print(f"Missing text values: {df['text'].isna().sum()}")
    print(f"Missing label values: {df['label'].isna().sum()}")
    
    # Remove rows with missing text
    df = df.dropna(subset=['text'])
    
    # Preprocess text
    print("Preprocessing text...")
    df['processed_text'] = df['text'].apply(preprocess_text)
    
    # Remove empty processed texts
    df = df[df['processed_text'] != '']
    
    print(f"Final dataset size: {len(df)} messages")
    print(f"Label distribution:\n{df['label'].value_counts()}")
    
    # Check if we have both classes
    unique_labels = df['label'].unique()
    print(f"Unique labels found: {unique_labels}")
    
    # Filter out any rows where label is not 'regular' or 'spam'
    df = df[df['label'].isin(['regular', 'spam'])]
    print(f"After filtering valid labels: {len(df)} messages")
    
    if len(df) == 0:
        print("Error: No valid messages found after filtering")
        return None
    
    # Check if we have both classes
    unique_labels = df['label'].unique()
    if len(unique_labels) < 2:
        print("Error: Need at least 2 different labels (regular and spam)")
        print(f"Available labels: {unique_labels}")
        return None
    
    # Check minimum samples per class
    label_counts = df['label'].value_counts()
    min_samples = label_counts.min()
    if min_samples < 2:
        print(f"Error: Need at least 2 samples per class. Current minimum: {min_samples}")
        print(f"Label distribution: {label_counts.to_dict()}")
        return None
    
    return df

def train_models(X_train, X_test, y_train, y_test):
    """
    Train multiple ML models and compare performance
    """
    models = {
        'Naive Bayes': MultinomialNB(),
        'Logistic Regression': LogisticRegression(max_iter=5000, random_state=100),
        'Random Forest': RandomForestClassifier(n_estimators=5000, random_state=100, max_depth=10)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate accuracy
        accuracy = accuracy_score(y_test, y_pred)
        
        # Store results
        results[name] = {
            'model': model,
            'accuracy': accuracy,
            'predictions': y_pred
        }
        
        print(f"{name} Accuracy: {accuracy:.4f}")
        
        # Print detailed classification report
        print(f"\n{name} Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Print confusion matrix
        print(f"{name} Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
    
    return results

def save_best_model(results, vectorizer, filename='data/training/spam_detection_model.pkl'):
    """
    Save the best performing model
    """
    # Find the best model
    best_model_name = max(results.keys(), key=lambda x: results[x]['accuracy'])
    best_model = results[best_model_name]['model']
    best_accuracy = results[best_model_name]['accuracy']
    
    print(f"\nBest model: {best_model_name} (Accuracy: {best_accuracy:.4f})")
    
    # Save the model and vectorizer
    model_data = {
        'model': best_model,
        'vectorizer': vectorizer,
        'model_name': best_model_name,
        'accuracy': best_accuracy
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"Model saved to {filename}")
    
    return best_model_name, best_accuracy

def predict_spam(text, model_file='data/training/spam_detection_model.pkl'):
    """
    Predict if a message is spam or regular
    """
    try:
        # Load the model
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        vectorizer = model_data['vectorizer']
        
        # Preprocess the text
        processed_text = preprocess_text(text)
        
        # Vectorize the text
        text_vectorized = vectorizer.transform([processed_text])
        
        # Make prediction
        prediction = model.predict(text_vectorized)[0]
        probability = model.predict_proba(text_vectorized)[0]
        
        return prediction, probability
        
    except FileNotFoundError:
        print(f"Model file {model_file} not found. Please train the model first.")
        return None, None
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None, None

def main():
    """
    Main function to train the spam detection model
    """
    print("=== GroupMe Spam Detection Model Training ===\n")
    
    # Load and prepare data
    df = load_and_prepare_data()
    
    if df is None:
        return
    
    # Split the data
    print("\nSplitting data into training and testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        df['processed_text'], 
        df['label'], 
        test_size=0.2, 
        random_state=42,
        stratify=df['label']
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Testing set size: {len(X_test)}")
    
    # Vectorize the text
    print("\nVectorizing text data...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=2,
        max_df=0.95
    )
    
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    print(f"Feature matrix shape: {X_train_vectorized.shape}")
    
    # Train models
    print("\nTraining models...")
    results = train_models(X_train_vectorized, X_test_vectorized, y_train, y_test)
    
    # Save the best model
    print("\nSaving best model...")
    best_model_name, best_accuracy = save_best_model(results, vectorizer)
    
    print(f"\n=== Training Complete ===")
    print(f"Best model: {best_model_name}")
    print(f"Best accuracy: {best_accuracy:.4f}")
    
    # Test the model with some example messages
    print("\n=== Testing with example messages ===")
    test_messages = [
        "Hey everyone, how's it going?",
        "FREE MONEY NOW! CLICK HERE!",
        "What time is the meeting tomorrow?",
        "URGENT: You've won $1000! Claim now!",
        "Thanks for the update on the project",
        "Hi guys I’m looking to sell my full season tickets message me if interested (302) 899-3327."
        "If you guys need football tickets just text me at 770-234-1111",
        "Hi guys I’m looking to sell my full season tickets message me if interested (302) 899-3327",
    ]
    
    for message in test_messages:
        prediction, probability = predict_spam(message)
        if prediction is not None:
            confidence = max(probability)
            print(f"Message: '{message[:50]}...'")
            print(f"Prediction: {prediction} (Confidence: {confidence:.3f})")
            print()

if __name__ == "__main__":
    main()
