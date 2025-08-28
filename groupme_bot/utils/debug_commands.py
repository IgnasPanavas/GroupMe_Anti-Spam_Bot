#!/usr/bin/env python3
"""
Debug script to test the command system
"""

import os
from dotenv import load_dotenv
from chat_commands import ChatCommands

# Load environment variables
load_dotenv()

def test_command_system():
    """Test the command system with debug output"""
    
    # Get BOT_USER_ID from environment
    bot_user_id = os.environ.get("BOT_USER_ID", "unknown")
    print(f"BOT_USER_ID from environment: '{bot_user_id}'")
    
    # Initialize chat commands
    chat_commands = ChatCommands(bot_user_id)
    
    # Test cases
    test_cases = [
        {
            "message": "/spam-bot: help",
            "sender_id": "user_123",
            "sender_name": "Test User",
            "group_id": "109638241",
            "group_name": "Test Group"
        },
        {
            "message": "/spam-bot: status",
            "sender_id": "user_456",
            "sender_name": "Another User",
            "group_id": "109638241",
            "group_name": "Test Group"
        }
    ]
    
    print("\n=== Testing Command System ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"Message: '{test_case['message']}'")
        print(f"Sender: {test_case['sender_name']} ({test_case['sender_id']})")
        
        # Test command detection
        is_command = chat_commands.is_command(test_case['message'])
        print(f"Is Command: {is_command}")
        
        if is_command:
            # Test command execution
            response = chat_commands.execute_command(
                test_case['message'],
                test_case['sender_id'],
                test_case['sender_name'],
                test_case['group_id'],
                test_case['group_name']
            )
            print(f"Response: {response}")
        else:
            print("Not a command")
        
        print("-" * 50)

if __name__ == "__main__":
    test_command_system()
