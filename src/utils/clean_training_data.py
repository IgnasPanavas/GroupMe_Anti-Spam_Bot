#!/usr/bin/env python3
"""
Clean up the master training data CSV file
"""

import pandas as pd
import os
import re
from datetime import datetime

def clean_master_training_data(input_file='data/training/master_training_data.csv', output_file='data/training/master_training_data_clean.csv', max_regular_messages=1000):
    """
    Clean the master training data by removing duplicates, spam, and limiting data size
    
    Args:
        input_file (str): Input CSV file to clean
        output_file (str): Output CSV file for cleaned data
        max_regular_messages (int): Maximum number of regular messages to keep
    """
    print(f"Cleaning {input_file}...")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return False
    
    # Load the data
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} messages from {input_file}")
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return False
    
    # Check initial data
    print(f"Initial data shape: {df.shape}")
    print(f"Label distribution:\n{df['label'].value_counts()}")
    
    # Step 1: Remove rows with missing or empty text
    df = df.dropna(subset=['text'])
    df = df[df['text'].str.strip() != '']
    print(f"After removing empty text: {len(df)} messages")
    
    # Step 2: Remove duplicate messages (exact text matches)
    df = df.drop_duplicates(subset=['text'])
    print(f"After removing duplicates: {len(df)} messages")
    
    # Step 3: Remove spam messages from regular dataset
    # Common spam patterns
    spam_patterns = [
        r'ps5|playstation|gaming system',
        r'macbook|mac book|laptop.*free',
        r'car.*sell|selling.*car',
        r'phone.*number|call.*\d{3}[-.]?\d{3}[-.]?\d{4}',
        r'email.*@.*\.com',
        r'tickets.*sell|selling.*tickets',
        r'free.*giveaway|giveaway.*free',
        r'urgent.*need|need.*urgent',
        r'limited.*time|time.*limited',
        r'first.*come.*first.*serve',
        r'dm.*interested|interested.*dm',
        r'contact.*number|number.*contact'
    ]
    
    # Create spam detection function
    def is_spam_message(text):
        if pd.isna(text):
            return False
        text_lower = str(text).lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    # Remove messages that look like spam from regular dataset
    regular_messages = df[df['label'] == 'regular'].copy()
    spam_messages = df[df['label'] == 'spam'].copy()
    
    # Check regular messages for spam patterns
    regular_messages['is_spam_pattern'] = regular_messages['text'].apply(is_spam_message)
    spam_in_regular = regular_messages[regular_messages['is_spam_pattern'] == True]
    
    if len(spam_in_regular) > 0:
        print(f"Found {len(spam_in_regular)} spam-like messages in regular dataset:")
        for _, row in spam_in_regular.head(5).iterrows():
            print(f"  - {row['text'][:100]}...")
    
    # Remove spam patterns from regular messages
    regular_messages = regular_messages[regular_messages['is_spam_pattern'] == False]
    regular_messages = regular_messages.drop('is_spam_pattern', axis=1)
    
    print(f"After removing spam patterns from regular: {len(regular_messages)} messages")
    
    # Step 4: Limit regular messages to prevent excessive data
    if len(regular_messages) > max_regular_messages:
        print(f"Limiting regular messages from {len(regular_messages)} to {max_regular_messages}")
        regular_messages = regular_messages.sample(n=max_regular_messages, random_state=42)
    
    # Step 5: Combine cleaned data
    cleaned_df = pd.concat([regular_messages, spam_messages], ignore_index=True)
    
    # Step 6: Remove very short messages (likely not useful for training)
    cleaned_df = cleaned_df[cleaned_df['text'].str.len() > 3]
    
    # Step 7: Remove very long messages (likely not useful for training)
    cleaned_df = cleaned_df[cleaned_df['text'].str.len() < 500]
    
    print(f"After length filtering: {len(cleaned_df)} messages")
    
    # Final statistics
    print(f"\nFinal cleaned data:")
    print(f"Total messages: {len(cleaned_df)}")
    print(f"Label distribution:\n{cleaned_df['label'].value_counts()}")
    
    # Save cleaned data
    try:
        cleaned_df.to_csv(output_file, index=False)
        print(f"Cleaned data saved to {output_file}")
        
        # Create backup of original file
        backup_file = f"master_training_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(backup_file, index=False)
        print(f"Original data backed up to {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"Error saving cleaned data: {e}")
        return False

def replace_master_with_clean(clean_file='data/training/master_training_data_clean.csv'):
    """
    Replace the master training data with the cleaned version
    
    Args:
        clean_file (str): Path to the cleaned CSV file
    """
    if not os.path.exists(clean_file):
        print(f"Error: {clean_file} not found!")
        return False
    
    try:
        # Remove old master file
        if os.path.exists('data/training/master_training_data.csv'):
            os.remove('data/training/master_training_data.csv')
            print("Removed old master_training_data.csv")
        
        # Rename clean file to master
        os.rename(clean_file, 'data/training/master_training_data.csv')
        print(f"Replaced master_training_data.csv with cleaned version")
        
        return True
        
    except Exception as e:
        print(f"Error replacing master file: {e}")
        return False

def analyze_training_data(file='data/training/master_training_data.csv'):
    """
    Analyze the current training data
    
    Args:
        file (str): Path to the CSV file to analyze
    """
    if not os.path.exists(file):
        print(f"Error: {file} not found!")
        return
    
    try:
        df = pd.read_csv(file)
        print(f"\n=== Analysis of {file} ===")
        print(f"Total messages: {len(df)}")
        print(f"Label distribution:\n{df['label'].value_counts()}")
        
        # Text length statistics
        df['text_length'] = df['text'].str.len()
        print(f"\nText length statistics:")
        print(f"Mean length: {df['text_length'].mean():.1f} characters")
        print(f"Median length: {df['text_length'].median():.1f} characters")
        print(f"Min length: {df['text_length'].min()} characters")
        print(f"Max length: {df['text_length'].max()} characters")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['text']).sum()
        print(f"\nDuplicate messages: {duplicates}")
        
        # Sample messages
        print(f"\nSample regular messages:")
        regular_samples = df[df['label'] == 'regular'].head(3)
        for _, row in regular_samples.iterrows():
            print(f"  - {row['text'][:100]}...")
        
        if 'spam' in df['label'].values:
            print(f"\nSample spam messages:")
            spam_samples = df[df['label'] == 'spam'].head(3)
            for _, row in spam_samples.iterrows():
                print(f"  - {row['text'][:100]}...")
        
    except Exception as e:
        print(f"Error analyzing {file}: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean master training data')
    parser.add_argument('--action', choices=['clean', 'replace', 'analyze'], default='clean',
                       help='Action to perform')
    parser.add_argument('--input', default='data/training/master_training_data.csv',
                       help='Input CSV file')
    parser.add_argument('--output', default='data/training/master_training_data_clean.csv',
                       help='Output CSV file')
    parser.add_argument('--max-regular', type=int, default=1000,
                       help='Maximum number of regular messages to keep')
    
    args = parser.parse_args()
    
    if args.action == 'clean':
        success = clean_master_training_data(args.input, args.output, args.max_regular)
        if success:
            print("\nCleaning completed successfully!")
        else:
            print("\nCleaning failed!")
    
    elif args.action == 'replace':
        success = replace_master_with_clean(args.output)
        if success:
            print("\nReplacement completed successfully!")
        else:
            print("\nReplacement failed!")
    
    elif args.action == 'analyze':
        analyze_training_data(args.input)

if __name__ == "__main__":
    main()
