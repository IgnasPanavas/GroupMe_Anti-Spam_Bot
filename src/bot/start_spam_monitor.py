#!/usr/bin/env python3
"""
Simple script to start the GroupMe spam monitor
"""

from spam_monitor import SpamMonitor
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python start_spam_monitor.py <group_id>")
        print("Example: python start_spam_monitor.py 102419548")
        sys.exit(1)
    
    group_id = sys.argv[1]
    
    # Default settings
    confidence_threshold = 0.8  # 80% confidence required to remove spam
    check_interval = 10  # Check every 30 seconds
    
    print(f"Starting spam monitor for group: {group_id}")
    print(f"Confidence threshold: {confidence_threshold}")
    print(f"Check interval: {check_interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        monitor = SpamMonitor(
            group_id=group_id,
            confidence_threshold=confidence_threshold
        )
        
        monitor.run_monitor(check_interval=check_interval)
        
    except KeyboardInterrupt:
        print("\nSpam monitor stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
