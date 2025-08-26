#!/usr/bin/env python3
"""
GroupMe Anti-Spam Bot - Data Collection Script
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.groupme_api import get_messages_and_save_to_training, get_group_id_by_name

def main():
    """Main entry point for collecting training data"""
    print("=== GroupMe Anti-Spam Bot - Data Collection ===\n")
    
    # Example: Collect data from a specific group
    group_name = "Athens Student Investor Club"  # Change this to your group name
    
    try:
        group_id = get_group_id_by_name(group_name)
        if group_id:
            print(f"Found group: {group_name} (ID: {group_id})")
            get_messages_and_save_to_training(group_id, limit=300, label="regular", max_messages=1000)
        else:
            print(f"Group '{group_name}' not found!")
            return 1
            
    except Exception as e:
        print(f"Data collection failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
