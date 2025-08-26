#!/usr/bin/env python3
"""
GroupMe Anti-Spam Bot - Data Cleanup Script
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.clean_training_data import clean_master_training_data, replace_master_with_clean, analyze_training_data

def main():
    """Main entry point for cleaning training data"""
    print("=== GroupMe Anti-Spam Bot - Data Cleanup ===\n")
    
    # Step 1: Analyze current data
    print("1. Analyzing current data...")
    analyze_training_data('data/training/master_training_data.csv')
    
    # Step 2: Clean the data
    print("\n2. Cleaning data...")
    success = clean_master_training_data(
        input_file='data/training/master_training_data.csv',
        output_file='data/training/master_training_data_clean.csv',
        max_regular_messages=800  # Keep 800 regular messages
    )
    
    if not success:
        print("Cleaning failed!")
        return 1
    
    # Step 3: Replace with cleaned version
    print("\n3. Replacing with cleaned version...")
    success = replace_master_with_clean('data/training/master_training_data_clean.csv')
    
    if success:
        print("\n4. Final analysis of cleaned data...")
        analyze_training_data('data/training/master_training_data.csv')
        print("\n✅ Data cleaning completed successfully!")
    else:
        print("\n❌ Failed to replace with cleaned version!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
