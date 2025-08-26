#!/usr/bin/env python3
"""
GroupMe Anti-Spam Bot - Training Script
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ml.model_trainer import train_models

def main():
    """Main entry point for training the spam detection model"""
    print("=== GroupMe Anti-Spam Bot - Model Training ===\n")
    
    try:
        # Train the model
        train_models()
        print("\n✅ Model training completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Model training failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
