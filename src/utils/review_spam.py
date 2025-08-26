#!/usr/bin/env python3
"""
Script to review and manage spam messages that couldn't be automatically removed
"""

import pandas as pd
import os
from datetime import datetime

def show_pending_spam():
    """Show all pending spam messages for review"""
    spam_log_file = "spam_review_log.csv"
    
    if not os.path.exists(spam_log_file):
        print("No spam review log found.")
        return
    
    try:
        df = pd.read_csv(spam_log_file)
        pending = df[df['status'] == 'pending_review']
        
        if len(pending) == 0:
            print("No pending spam messages for review.")
            return
        
        print(f"\n=== Pending Spam Review ({len(pending)} messages) ===")
        print("=" * 80)
        
        for idx, row in pending.iterrows():
            print(f"\n{idx + 1}. Message ID: {row['message_id']}")
            print(f"   From: {row['sender_name']} ({row['sender_id']})")
            print(f"   Time: {row['timestamp']}")
            print(f"   Confidence: {row['confidence']}")
            print(f"   Text: {row['text'][:100]}{'...' if len(row['text']) > 100 else ''}")
            print(f"   Group ID: {row['group_id']}")
            print("-" * 40)
        
    except Exception as e:
        print(f"Error reading spam log: {e}")

def mark_as_reviewed(message_id, action='removed'):
    """
    Mark a spam message as reviewed
    
    Args:
        message_id (str): The message ID to mark
        action (str): Action taken ('removed', 'ignored', 'false_positive')
    """
    spam_log_file = "spam_review_log.csv"
    
    if not os.path.exists(spam_log_file):
        print("No spam review log found.")
        return
    
    try:
        df = pd.read_csv(spam_log_file)
        
        # Find the message
        mask = df['message_id'] == message_id
        if not mask.any():
            print(f"Message ID {message_id} not found in spam log.")
            return
        
        # Update status
        df.loc[mask, 'status'] = f"reviewed_{action}"
        df.to_csv(spam_log_file, index=False)
        
        print(f"Marked message {message_id} as reviewed with action: {action}")
        
    except Exception as e:
        print(f"Error updating spam log: {e}")

def show_statistics():
    """Show statistics about spam detection"""
    spam_log_file = "spam_review_log.csv"
    
    if not os.path.exists(spam_log_file):
        print("No spam review log found.")
        return
    
    try:
        df = pd.read_csv(spam_log_file)
        
        print("\n=== Spam Detection Statistics ===")
        print("=" * 40)
        
        total_messages = len(df)
        pending_review = len(df[df['status'] == 'pending_review'])
        reviewed_removed = len(df[df['status'] == 'reviewed_removed'])
        reviewed_ignored = len(df[df['status'] == 'reviewed_ignored'])
        false_positives = len(df[df['status'] == 'reviewed_false_positive'])
        
        print(f"Total spam messages detected: {total_messages}")
        print(f"Pending review: {pending_review}")
        print(f"Reviewed and removed: {reviewed_removed}")
        print(f"Reviewed and ignored: {reviewed_ignored}")
        print(f"False positives: {false_positives}")
        
        if total_messages > 0:
            false_positive_rate = (false_positives / total_messages) * 100
            print(f"False positive rate: {false_positive_rate:.1f}%")
        
    except Exception as e:
        print(f"Error reading statistics: {e}")

def interactive_review():
    """Interactive spam review mode"""
    spam_log_file = "spam_review_log.csv"
    
    if not os.path.exists(spam_log_file):
        print("No spam review log found.")
        return
    
    try:
        df = pd.read_csv(spam_log_file)
        pending = df[df['status'] == 'pending_review']
        
        if len(pending) == 0:
            print("No pending spam messages for review.")
            return
        
        print(f"\n=== Interactive Spam Review ===")
        print("Commands: 'r' = remove, 'i' = ignore, 'f' = false positive, 'q' = quit")
        print("=" * 50)
        
        for idx, row in pending.iterrows():
            print(f"\nMessage {idx + 1}/{len(pending)}:")
            print(f"From: {row['sender_name']}")
            print(f"Text: {row['text'][:100]}{'...' if len(row['text']) > 100 else ''}")
            print(f"Confidence: {row['confidence']}")
            
            while True:
                action = input("Action (r/i/f/q): ").lower().strip()
                
                if action == 'q':
                    print("Review session ended.")
                    return
                elif action == 'r':
                    mark_as_reviewed(row['message_id'], 'removed')
                    break
                elif action == 'i':
                    mark_as_reviewed(row['message_id'], 'ignored')
                    break
                elif action == 'f':
                    mark_as_reviewed(row['message_id'], 'false_positive')
                    break
                else:
                    print("Invalid action. Use 'r', 'i', 'f', or 'q'.")
        
        print("All pending messages reviewed!")
        
    except Exception as e:
        print(f"Error in interactive review: {e}")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python review_spam.py show          - Show pending spam")
        print("  python review_spam.py stats         - Show statistics")
        print("  python review_spam.py review        - Interactive review")
        print("  python review_spam.py mark <id> <action> - Mark message as reviewed")
        print("    Actions: removed, ignored, false_positive")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_pending_spam()
    elif command == 'stats':
        show_statistics()
    elif command == 'review':
        interactive_review()
    elif command == 'mark':
        if len(sys.argv) < 4:
            print("Usage: python review_spam.py mark <message_id> <action>")
            return
        message_id = sys.argv[2]
        action = sys.argv[3]
        mark_as_reviewed(message_id, action)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
