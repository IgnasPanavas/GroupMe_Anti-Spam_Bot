#!/usr/bin/env python3
"""
Retrain the spam detection model with a properly fitted TF-IDF vectorizer
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import os

def retrain_model():
    """Retrain the spam detection model with properly fitted vectorizer"""
    
    print("🔄 Starting model retraining...")
    
    # Load the balanced training data (has both spam and ham examples)
    training_file = 'data/training/balanced_training_data_20250829_121432.csv'
    
    if not os.path.exists(training_file):
        print(f"❌ Training file not found: {training_file}")
        return False
    
    try:
        # Load the training data
        print(f"📊 Loading training data from: {training_file}")
        df = pd.read_csv(training_file)
        print(f"✅ Loaded {len(df)} training samples")
        
        # Check the data structure
        print(f"📋 Columns: {df.columns.tolist()}")
        print(f"🏷️  Label distribution:")
        label_counts = df['label'].value_counts()
        for label, count in label_counts.items():
            print(f"   {label}: {count} samples")
        
        # Prepare the data
        X = df['text'].fillna('').astype(str)
        y = df['label'].fillna('ham')  # Default to 'ham' for missing labels
        
        print(f"📝 X shape: {X.shape}, y shape: {y.shape}")
        
        # Split the data
        print("✂️  Splitting data into train/test sets...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📚 Training set: {len(X_train)} samples")
        print(f"🧪 Test set: {len(X_test)} samples")
        
        # Create and fit the TF-IDF vectorizer
        print("🔤 Creating and fitting TF-IDF vectorizer...")
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            lowercase=True
        )
        
        # Fit the vectorizer on training data
        print("⚙️  Fitting vectorizer to training data...")
        X_train_tfidf = vectorizer.fit_transform(X_train)
        print(f"✅ Vectorizer fitted successfully!")
        print(f"📚 Vocabulary size: {len(vectorizer.vocabulary_)}")
        print(f"🔢 IDF vector length: {len(vectorizer.idf_)}")
        
        # Transform test data
        print("🔄 Transforming test data...")
        X_test_tfidf = vectorizer.transform(X_test)
        print(f"✅ Test data transformed successfully!")
        
        # Train the classifier
        print("🤖 Training Random Forest classifier...")
        classifier = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            n_jobs=-1
        )
        classifier.fit(X_train_tfidf, y_train)
        print(f"✅ Classifier trained successfully!")
        
        # Evaluate the model
        print("📊 Evaluating model performance...")
        y_pred = classifier.predict(X_test_tfidf)
        
        print("\n📈 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\n🔢 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # Test the vectorizer to ensure it's properly fitted
        print("\n🧪 Testing vectorizer functionality...")
        test_text = "test message for spam detection"
        try:
            test_features = vectorizer.transform([test_text])
            print(f"✅ Vectorizer transform successful! Features shape: {test_features.shape}")
        except Exception as e:
            print(f"❌ Vectorizer transform failed: {e}")
            return False
        
        # Save the properly fitted vectorizer and model
        output_dir = 'data/training'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save vectorizer
        vectorizer_path = os.path.join(output_dir, 'tfidf_vectorizer.pkl')
        print(f"💾 Saving vectorizer to: {vectorizer_path}")
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        
        # Save model
        model_path = os.path.join(output_dir, 'spam_detection_model.pkl')
        print(f"💾 Saving model to: {model_path}")
        with open(model_path, 'wb') as f:
            pickle.dump(classifier, f)
        
        # Verify the saved files
        print("\n🔍 Verifying saved files...")
        try:
            with open(vectorizer_path, 'rb') as f:
                test_vectorizer = pickle.load(f)
            
            with open(model_path, 'rb') as f:
                test_model = pickle.load(f)
            
            # Test the loaded vectorizer
            test_features = test_vectorizer.transform([test_text])
            test_prediction = test_model.predict(test_features)
            
            print(f"✅ Loaded vectorizer transform successful! Features shape: {test_features.shape}")
            print(f"✅ Loaded model prediction successful! Prediction: {test_prediction[0]}")
            
        except Exception as e:
            print(f"❌ Error verifying saved files: {e}")
            return False
        
        print("\n🎉 Model retraining completed successfully!")
        print(f"📁 Vectorizer saved to: {vectorizer_path}")
        print(f"📁 Model saved to: {model_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error retraining model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 SpamShield Model Retraining Script")
    print("=" * 50)
    
    success = retrain_model()
    
    if success:
        print("\n✅ Model retraining completed successfully!")
        print("🔄 You can now rebuild and redeploy the Lambda function.")
    else:
        print("\n❌ Model retraining failed!")
        print("🔍 Check the error messages above for details.")
