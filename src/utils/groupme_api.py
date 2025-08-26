import requests
import os
from dotenv import load_dotenv
import json
import csv
import pandas as pd
from datetime import datetime

load_dotenv()

BASE_URI = "https://api.groupme.com/v3"

API_KEY = os.environ["API_KEY"]
BOT_USER_ID = os.environ.get("BOT_USER_ID")

def get_groups():
    COMPLETE_URI = f"{BASE_URI}/groups?token={API_KEY}"
    HEADERS= {"Content-Type":"application/json"}
    response = requests.get(COMPLETE_URI,headers=HEADERS)

    print(response.status_code)
    print(response.text)
    save_response_to_json(response)
    
def save_response_to_json(response):
    try:
        # Parse the response text as JSON
        response_data = response.json()
        
        # Create a filename with timestamp or use a default name
        filename = "groups_response.json"
        
        # Write the response data to a JSON file
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(response_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"Response saved to {filename}")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        # If response is not valid JSON, save the raw text
        with open("response_text.txt", 'w', encoding='utf-8') as text_file:
            text_file.write(response.text)
        print("Raw response text saved to response_text.txt")
    except Exception as e:
        print(f"Error saving response: {e}")

def find_admin_groups():
    """
    Find and print the names of groups where the user (BOT_USERNAME) is an admin
    """
    if not BOT_USER_ID:
        print("Error: BOT_USER_ID not found in environment variables")
        return
    
    COMPLETE_URI = f"{BASE_URI}/groups?token={API_KEY}"
    HEADERS = {"Content-Type": "application/json"}
    
    try:
        response = requests.get(COMPLETE_URI, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_data = response.json()
        
        if 'response' not in response_data:
            print("Error: Unexpected response format")
            return
        
        groups = response_data['response']
        admin_groups = []
        
        for group in groups:
            # Check if the user is in the members list and is an admin
            if 'members' in group:
                for member in group['members']:
                    # Check if this member is the bot user and is an admin
                    if (member.get('user_id') == BOT_USER_ID and 
                        member.get('role') == 'admin'):
                        admin_groups.append({
                            'name': group.get('name', 'Unknown'),
                            'group_id': group.get('group_id'),
                            'description': group.get('description', 'No description')
                        })
                        break  # Found the user in this group, move to next group
        
        # Print results
        if admin_groups:
            print(f"\nGroups where {BOT_USER_ID} is an admin:")
            print("=" * 50)
            for i, group in enumerate(admin_groups, 1):
                print(f"{i}. {group['name']}")
                print(f"   Group ID: {group['group_id']}")
                if group['description']:
                    print(f"   Description: {group['description']}")
                print()
        else:
            print(f"\nNo groups found where {BOT_USER_ID} is an admin.")
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def find_group_by_name(group_name):
    """
    Find a group ID by searching through group names
    
    Args:
        group_name (str): The name of the group to search for (case-insensitive)
    
    Returns:
        dict: Group information if found, None otherwise
    """
    if not group_name:
        print("Error: Group name is required")
        return None
    
    COMPLETE_URI = f"{BASE_URI}/groups?token={API_KEY}"
    HEADERS = {"Content-Type": "application/json"}
    
    try:
        response = requests.get(COMPLETE_URI, headers=HEADERS)
        response.raise_for_status()
        
        response_data = response.json()
        
        if 'response' not in response_data:
            print("Error: Unexpected response format")
            return None
        
        groups = response_data['response']
        group_name_lower = group_name.lower()
        
        # Search for exact or partial matches
        exact_matches = []
        partial_matches = []
        
        for group in groups:
            current_name = group.get('name', '')
            current_name_lower = current_name.lower()
            
            # Check for exact match
            if current_name_lower == group_name_lower:
                exact_matches.append(group)
            # Check for partial match
            elif group_name_lower in current_name_lower:
                partial_matches.append(group)
        
        # Print results
        if exact_matches:
            print(f"\nExact matches for '{group_name}':")
            print("=" * 60)
            for i, group in enumerate(exact_matches, 1):
                print(f"{i}. {group['name']}")
                print(f"   Group ID: {group['group_id']}")
                print(f"   Members: {group.get('members_count', 'Unknown')}")
                if group.get('description'):
                    print(f"   Description: {group['description']}")
                print()
        
        if partial_matches and not exact_matches:
            print(f"\nPartial matches for '{group_name}':")
            print("=" * 60)
            for i, group in enumerate(partial_matches, 1):
                print(f"{i}. {group['name']}")
                print(f"   Group ID: {group['group_id']}")
                print(f"   Members: {group.get('members_count', 'Unknown')}")
                if group.get('description'):
                    print(f"   Description: {group['description']}")
                print()
        
        if not exact_matches and not partial_matches:
            print(f"\nNo groups found matching '{group_name}'")
            return None
        
        # Return the first exact match, or first partial match if no exact matches
        if exact_matches:
            return exact_matches[0]
        else:
            return partial_matches[0]
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def get_group_id_by_name(group_name):
    """
    Get just the group ID by name
    
    Args:
        group_name (str): The name of the group to search for
    
    Returns:
        str: Group ID if found, None otherwise
    """
    group_info = find_group_by_name(group_name)
    if group_info:
        return group_info['group_id']
    return None

def get_messages_from_group(group_id, limit=100):
    """
    Pull the last (limit) number of real user messages from a specific group,
    excluding system messages from GroupMe
    
    Args:
        group_id (str): The ID of the group to get messages from
        limit (int): Number of real user messages to retrieve (default: 100, no maximum)
    """
    if not group_id:
        print("Error: Group ID is required")
        return
    
    # Ensure limit is at least 1
    if limit < 1:
        print("Error: Limit must be at least 1")
        return
    
    real_user_messages = []
    before_id = None
    total_fetched = 0
    
    print(f"Fetching {limit} real user messages from group {group_id}...")
    
    while len(real_user_messages) < limit:
        # Build the API URL with pagination
        if before_id:
            COMPLETE_URI = f"{BASE_URI}/groups/{group_id}/messages?token={API_KEY}&limit=100&before_id={before_id}"
        else:
            COMPLETE_URI = f"{BASE_URI}/groups/{group_id}/messages?token={API_KEY}&limit=100"
        
        HEADERS = {"Content-Type": "application/json"}
        
        try:
            response = requests.get(COMPLETE_URI, headers=HEADERS)
            response.raise_for_status()
            
            response_data = response.json()
            
            if 'response' not in response_data:
                print("Error: Unexpected response format")
                return
            
            if response_data['response'] is None:
                print("Error: Response data is None")
                return
            
            if 'messages' not in response_data['response']:
                print("Error: No messages field in response")
                return
            
            messages = response_data['response']['messages']
            total_fetched += len(messages)
            
            # If no more messages, break
            if not messages:
                print("No more messages available")
                break
            
            # Filter out system messages from GroupMe
            for message in messages:
                sender_name = message.get('name', 'Unknown')
                user_id = message.get('user_id', '')
                text = message.get('text', '')
                
                # Skip messages from GroupMe system (user_id is typically empty or specific for system messages)
                # Also skip messages that are join/leave notifications
                if (sender_name == 'GroupMe' or 
                    not user_id or 
                    (text and 'has joined the group' in text) or
                    (text and 'has left the group' in text) or
                    (text and 'has been removed from the group' in text) or
                    (text and 'has been added to the group' in text) or
                    (text and 'This message was deleted' in text) or
                    (text and 'This message was removed' in text) or 
                    (text and 'An admin deleted this message' in text)):
                    continue
                
                real_user_messages.append(message)
                
                # Stop if we have enough real user messages
                if len(real_user_messages) >= limit:
                    break
            
            # Get the ID of the last message for pagination
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if last_message and 'id' in last_message:
                    before_id = last_message['id']
                else:
                    print("Warning: Last message missing ID, stopping pagination")
                    break
            else:
                print("No messages in response, stopping pagination")
                break
            
            # If we got fewer messages than requested, we might be at the end
            if len(messages) < 100:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    # Print message summary
    print(f"\nRetrieved {len(real_user_messages)} real user messages (fetched {total_fetched} total messages):")
    print("=" * 80)
    
    for i, message in enumerate(real_user_messages, 1):
        sender_name = message.get('name', 'Unknown')
        text = message.get('text', '')
        created_at = message.get('created_at', 0)
        
        # Convert timestamp to readable format
        if created_at:
            date_str = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_str = 'Unknown time'
        
        print(f"{i}. {sender_name} ({date_str}):")
        if text:
            # Truncate long messages for display
            display_text = text[:100] + "..." if len(text) > 100 else text
            print(f"   {display_text}")
        else:
            print("   [No text content]")
        print()
    
    # Save real user messages to JSON file
    filename = f"real_user_messages_group_{group_id}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump({
                'meta': {'code': 200},
                'response': {
                    'messages': real_user_messages,
                    'count': len(real_user_messages)
                }
            }, json_file, indent=2, ensure_ascii=False)
        print(f"Real user messages saved to {filename}")
    except Exception as e:
        print(f"Error saving messages to file: {e}")
        
    return real_user_messages
        

def save_messages_to_training_csv(messages, group_id, label="regular", max_messages=1000):
    """
    Save messages directly to master training CSV file with size limits and deduplication
    
    Args:
        messages (list): List of message dictionaries
        group_id (str): The group ID for reference
        label (str): The label for the messages (default: "regular")
        max_messages (int): Maximum number of messages to keep in the file
    """
    if not messages:
        print("No messages to save to training data")
        return
    
    # Master training file
    master_filename = "data/training/master_training_data.csv"
    file_exists = os.path.exists(master_filename)
    
    # Load existing data if file exists
    existing_messages = set()
    existing_count = 0
    
    if file_exists:
        try:
            existing_df = pd.read_csv(master_filename)
            existing_count = len(existing_df)
            existing_messages = set(existing_df['text'].dropna().astype(str))
            print(f"Found existing {existing_count} messages in {master_filename}")
        except Exception as e:
            print(f"Warning: Could not read existing file: {e}")
            existing_messages = set()
    
    # Filter out duplicates and empty messages
    new_messages = []
    for message in messages:
        text = message.get('text', '').strip()
        if text and text not in existing_messages:
            new_messages.append({
                'text': text,
                'label': label
            })
            existing_messages.add(text)
    
    if not new_messages:
        print("No new unique messages to add")
        return
    
    print(f"Adding {len(new_messages)} new unique messages")
    
    # Combine existing and new data
    if file_exists:
        try:
            existing_df = pd.read_csv(master_filename)
            new_df = pd.DataFrame(new_messages)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            print(f"Error reading existing file, creating new one: {e}")
            combined_df = pd.DataFrame(new_messages)
    else:
        combined_df = pd.DataFrame(new_messages)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['text'])
    
    # Limit total messages to prevent excessive data
    if len(combined_df) > max_messages:
        print(f"Limiting total messages from {len(combined_df)} to {max_messages}")
        # Keep a mix of regular and spam messages
        regular_messages = combined_df[combined_df['label'] == 'regular']
        spam_messages = combined_df[combined_df['label'] == 'spam']
        
        # Calculate how many of each to keep
        max_regular = int(max_messages * 0.8)  # 80% regular
        max_spam = max_messages - max_regular   # 20% spam
        
        if len(regular_messages) > max_regular:
            regular_messages = regular_messages.sample(n=max_regular, random_state=42)
        
        if len(spam_messages) > max_spam:
            spam_messages = spam_messages.sample(n=max_spam, random_state=42)
        
        combined_df = pd.concat([regular_messages, spam_messages], ignore_index=True)
    
    # Save the combined data
    try:
        combined_df.to_csv(master_filename, index=False)
        print(f"Saved {len(combined_df)} total messages to {master_filename}")
        print(f"Label distribution: {combined_df['label'].value_counts().to_dict()}")
        
    except Exception as e:
        print(f"Error saving to training CSV: {e}")

def get_messages_and_save_to_training(group_id, limit=300, label="regular", max_messages=1000):
    """
    Get messages from a group and save them to training data CSV
    
    Args:
        group_id (str): The group ID to get messages from
        limit (int): Number of real user messages to retrieve
        label (str): The label for the messages (default: "regular")
        max_messages (int): Maximum number of messages to keep in the file
    """
    print(f"Getting {limit} messages from group {group_id} for training data...")
    
    # Get the messages
    messages = get_messages_from_group(group_id, limit)
    
    if messages:
        # Save to training data CSV
        save_messages_to_training_csv(messages, group_id, label, max_messages)
    else:
        print("No messages retrieved for training data")


get_messages_and_save_to_training(get_group_id_by_name("Athens Student Investor Club"))