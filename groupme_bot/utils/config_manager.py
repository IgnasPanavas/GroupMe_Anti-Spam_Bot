#!/usr/bin/env python3
"""
Command system for the GroupMe Anti-Spam Bot
"""

import json
import os
from datetime import datetime

class BotCommands:
    def __init__(self, config_file='data/config/bot_config.json'):
        """
        Initialize the bot command system
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load bot configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "active_groups": [],
            "settings": {
                "confidence_threshold": 0.8,
                "check_interval": 30,
                "model_file": "data/training/spam_detection_model.pkl",
                "show_removal_messages": True,
                "show_startup_message": True
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def activate_group(self, group_id, group_name=None):
        """
        Activate the bot for a specific group
        
        Args:
            group_id (str): The group ID to activate
            group_name (str): Optional group name for reference
            
        Returns:
            bool: True if activated successfully, False otherwise
        """
        # Check if group is already active
        for group in self.config["active_groups"]:
            if group["group_id"] == group_id:
                print(f"Bot is already active for group {group_id}")
                return True
        
        group_info = {
            "group_id": group_id,
            "group_name": group_name or f"Group {group_id}",
            "activated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.config["active_groups"].append(group_info)
        
        if self.save_config():
            print(f"Bot activated for group {group_id} ({group_name or 'Unknown'})")
            return True
        else:
            print(f"Failed to activate bot for group {group_id}")
            return False
    
    def deactivate_group(self, group_id):
        """
        Deactivate the bot for a specific group
        
        Args:
            group_id (str): The group ID to deactivate
            
        Returns:
            bool: True if deactivated successfully, False otherwise
        """
        # Find and remove the group from active groups
        for i, group in enumerate(self.config["active_groups"]):
            if group["group_id"] == group_id:
                removed_group = self.config["active_groups"].pop(i)
                if self.save_config():
                    print(f"Bot deactivated for group {group_id} ({removed_group.get('group_name', 'Unknown')})")
                    return True
                else:
                    print(f"Failed to deactivate bot for group {group_id}")
                    return False
        
        print(f"Bot is not active for group {group_id}")
        return False
    
    def is_group_active(self, group_id):
        """
        Check if the bot is active for a specific group
        
        Args:
            group_id (str): The group ID to check
            
        Returns:
            bool: True if active, False otherwise
        """
        for group in self.config["active_groups"]:
            if group["group_id"] == group_id:
                return group.get("status", "active") == "active"
        return False
    
    def list_active_groups(self):
        """
        List all active groups
        
        Returns:
            list: List of active group information
        """
        if not self.config["active_groups"]:
            print("No active groups found.")
            return []
        
        print(f"\nActive Groups ({len(self.config['active_groups'])}):")
        print("=" * 60)
        
        for i, group in enumerate(self.config["active_groups"], 1):
            activated_at = group.get("activated_at", "Unknown")
            if activated_at != "Unknown":
                try:
                    dt = datetime.fromisoformat(activated_at)
                    activated_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            print(f"{i}. {group.get('group_name', 'Unknown')}")
            print(f"   Group ID: {group['group_id']}")
            print(f"   Status: {group.get('status', 'active')}")
            print(f"   Activated: {activated_at}")
            print()
        
        return self.config["active_groups"]
    
    def get_group_settings(self, group_id):
        """
        Get settings for a specific group
        
        Args:
            group_id (str): The group ID
            
        Returns:
            dict: Group settings or default settings if not found
        """
        for group in self.config["active_groups"]:
            if group["group_id"] == group_id:
                return group.get("settings", self.config["settings"])
        return self.config["settings"]
    
    def update_group_settings(self, group_id, settings):
        """
        Update settings for a specific group
        
        Args:
            group_id (str): The group ID
            settings (dict): New settings to apply
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        for group in self.config["active_groups"]:
            if group["group_id"] == group_id:
                group["settings"] = {**self.config["settings"], **settings}
                if self.save_config():
                    print(f"Settings updated for group {group_id}")
                    return True
                else:
                    print(f"Failed to update settings for group {group_id}")
                    return False
        
        print(f"Group {group_id} not found in active groups")
        return False
    
    def update_global_settings(self, settings):
        """
        Update global bot settings
        
        Args:
            settings (dict): New settings to apply
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        self.config["settings"].update(settings)
        if self.save_config():
            print("Global settings updated successfully")
            return True
        else:
            print("Failed to update global settings")
            return False
    
    def get_global_settings(self):
        """
        Get global bot settings
        
        Returns:
            dict: Global settings
        """
        return self.config["settings"]

def main():
    """Main function for command line interface"""
    import sys
    
    commands = BotCommands()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python bot_commands.py activate <group_id> [group_name]")
        print("  python bot_commands.py deactivate <group_id>")
        print("  python bot_commands.py list")
        print("  python bot_commands.py status <group_id>")
        return
    
    command = sys.argv[1].lower()
    
    if command == "activate":
        if len(sys.argv) < 3:
            print("Usage: python bot_commands.py activate <group_id> [group_name]")
            return
        group_id = sys.argv[2]
        group_name = sys.argv[3] if len(sys.argv) > 3 else None
        commands.activate_group(group_id, group_name)
    
    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("Usage: python bot_commands.py deactivate <group_id>")
            return
        group_id = sys.argv[2]
        commands.deactivate_group(group_id)
    
    elif command == "list":
        commands.list_active_groups()
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: python bot_commands.py status <group_id>")
            return
        group_id = sys.argv[2]
        is_active = commands.is_group_active(group_id)
        print(f"Group {group_id} is {'active' if is_active else 'inactive'}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
