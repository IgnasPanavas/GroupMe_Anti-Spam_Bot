#!/usr/bin/env python3
"""
Script to automatically detect and label spam in new raw message files.
Uses patterns from existing spam messages to identify similar spam.
"""

import pandas as pd
import re
import os
import glob
from datetime import datetime

class SpamDetector:
    def __init__(self, spam_reference_file="data/training/consolidated_spam_simplified.csv"):
        """Initialize the spam detector with reference spam data."""
        self.spam_patterns = []
        self.spam_keywords = set()
        self.phone_patterns = []
        
        # Load reference spam data
        if os.path.exists(spam_reference_file):
            self.load_spam_patterns(spam_reference_file)
        else:
            print(f"Warning: Spam reference file {spam_reference_file} not found!")
            self.load_default_patterns()
    
    def load_spam_patterns(self, spam_file):
        """Load and analyze spam patterns from reference file."""
        print(f"Loading spam patterns from: {spam_file}")
        
        df = pd.read_csv(spam_file)
        spam_messages = df[df['label'] == 'spam']['text'].tolist()
        
        # Extract common patterns
        for message in spam_messages:
            text = str(message).lower()
            
            # Extract keywords
            words = re.findall(r'\b\w+\b', text)
            self.spam_keywords.update(words)
            
            # Extract phone number patterns
            phone_patterns = re.findall(r'[\+]?1?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}', text)
            for pattern in phone_patterns:
                if pattern not in self.phone_patterns:
                    self.phone_patterns.append(pattern)
        
        # Create regex patterns for common spam indicators
        self.spam_patterns = [
            # Ticket sales (more specific)
            r'selling.*concert.*ticket',
            r'selling.*game.*ticket',
            r'looking.*sell.*concert.*ticket',
            r'looking.*sell.*game.*ticket',
            r'giving.*away.*concert.*ticket',
            r'passing.*concert.*ticket',
            r'passing.*game.*ticket',
            
            # Parking permits (more specific)
            r'selling.*parking.*permit.*text',
            r'selling.*parking.*pass.*text',
            r'buy.*permit.*text.*interested',
            r'parking.*permit.*text.*interested',
            
            # Electronics and items (more specific)
            r'selling.*macbook.*free',
            r'giving.*away.*macbook.*free',
            r'selling.*ps5.*free',
            r'giving.*away.*ps5.*free',
            r'selling.*car.*perfect.*condition',
            r'for sale.*perfect.*condition',
            
            # Contact patterns (more specific)
            r'text.*if.*interested.*\d{3}',
            r'text.*interested.*\d{3}',
            r'contact.*if.*interested.*\d{3}',
            r'hm.*interested.*\d{3}',
            r'hit.*up.*interested.*\d{3}',
            r'dm.*interested.*\d{3}',
            r'message.*interested.*\d{3}',
            
            # Suspicious offers (more specific)
            r'giving.*away.*free.*macbook',
            r'giving.*away.*free.*ps5',
            r'giving.*away.*free.*ticket',
            r'free.*macbook.*perfect.*condition',
            r'free.*ps5.*perfect.*condition',
            
            # Urgency indicators (more specific)
            r'first come first serve.*dm',
            r'strictly first come.*dm',
            r'dm now.*interested',
            r'text now.*interested',
            r'contact now.*interested',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.spam_patterns]
        
        print(f"Loaded {len(self.compiled_patterns)} spam patterns")
        print(f"Extracted {len(self.spam_keywords)} spam keywords")
        print(f"Found {len(self.phone_patterns)} phone number patterns")
    
    def load_default_patterns(self):
        """Load default spam patterns if no reference file exists."""
        print("Loading default spam patterns...")
        
        self.spam_patterns = [
            r'selling.*ticket',
            r'selling.*parking.*permit',
            r'text.*if.*interested',
            r'\+1\s*\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\(\d{3}\)\s*\d{3}[\s\-]?\d{4}',
            r'\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.spam_patterns]
    
    def is_spam(self, text):
        """Check if a message is spam based on patterns."""
        if not text or pd.isna(text):
            return False
        
        text_lower = str(text).lower()
        
        # Check for pattern matches
        pattern_matches = sum(1 for pattern in self.compiled_patterns if pattern.search(text_lower))
        
        # Check for keyword density
        words = re.findall(r'\b\w+\b', text_lower)
        spam_word_count = sum(1 for word in words if word in self.spam_keywords)
        keyword_density = spam_word_count / len(words) if words else 0
        
        # Scoring system
        score = 0
        
        # Pattern matches (weight: 3 each)
        score += pattern_matches * 3
        
        # Keyword density (weight: 10 if > 0.3)
        if keyword_density > 0.3:
            score += 10
        
        # Phone number presence (weight: 5)
        phone_pattern = re.compile(r'\+1\s*\d{3}[\s\-]?\d{3}[\s\-]?\d{4}|\(\d{3}\)\s*\d{3}[\s\-]?\d{4}|\d{3}[\s\-]?\d{3}[\s\-]?\d{4}')
        if phone_pattern.search(text_lower):
            score += 5
        
        # Email presence (weight: 3)
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        if email_pattern.search(text_lower):
            score += 3
        
        # Return True if score is high enough
        return score >= 15  # Much higher threshold to avoid false positives
    
    def detect_spam_in_file(self, csv_file, output_file=None):
        """Detect and label spam in a CSV file."""
        print(f"\nProcessing: {csv_file}")
        
        # Read the file
        df = pd.read_csv(csv_file)
        
        # Check if 'label' column exists, if not create it
        if 'label' not in df.columns:
            df['label'] = 'ham'  # Default to ham
        
        # Counter for changes
        changes_made = 0
        
        # Check each message
        for index, row in df.iterrows():
            text = row['text']
            
            # Skip if already labeled as spam
            if row['label'] == 'spam':
                continue
            
            # Check if it's spam
            if self.is_spam(text):
                df.at[index, 'label'] = 'spam'
                changes_made += 1
                print(f"  Detected spam: {text[:80]}...")
        
        # Save the updated file
        if output_file is None:
            output_file = csv_file
        
        df.to_csv(output_file, index=False)
        
        print(f"✅ Relabeled {changes_made} messages as spam in {output_file}")
        
        # Show summary
        label_counts = df['label'].value_counts()
        print(f"📊 Label distribution:")
        for label, count in label_counts.items():
            print(f"  {label}: {count} messages")
        
        return changes_made
    
    def detect_spam_in_directory(self, directory="data/raw_messages/"):
        """Detect spam in all CSV files in a directory."""
        csv_files = glob.glob(os.path.join(directory, "*.csv"))
        
        if not csv_files:
            print(f"No CSV files found in {directory}")
            return
        
        print(f"Processing {len(csv_files)} files in {directory}...")
        
        total_changes = 0
        
        for csv_file in csv_files:
            # Skip the consolidated spam file
            if "consolidated_spam" in csv_file:
                continue
                
            changes = self.detect_spam_in_file(csv_file)
            total_changes += changes
        
        print(f"\n🎯 Total spam messages detected: {total_changes}")

def main():
    """Main function to run spam detection."""
    detector = SpamDetector()
    
    # Detect spam in all raw message files
    detector.detect_spam_in_directory()

if __name__ == "__main__":
    main()
