#!/usr/bin/env python3
"""
Chat-based command system for the GroupMe Anti-Spam Bot
"""

import re
import logging
import requests
import os
import sys
from dotenv import load_dotenv

from groupme_bot.utils.config_manager import BotCommands
from groupme_bot.utils.groupme_api import get_group_id_by_name, find_group_by_name

load_dotenv()
BASE_URI = "https://api.groupme.com/v3"
API_KEY = os.environ["API_KEY"]

logger = logging.getLogger(__name__)

class ChatCommands:
    def __init__(self, bot_user_id):
        """
        Initialize the chat command system
        
        Args:
            bot_user_id (str): The bot's user ID to identify its own messages
        """
        self.bot_user_id = bot_user_id
        self.commands = BotCommands()
        self.command_prefix = "/spam-bot:"
        self.last_processed_command = None  # Track the last command processed
        
        # Define available commands
        self.available_commands = {
            "activate": self._cmd_activate,
            "deactivate": self._cmd_deactivate,
            "status": self._cmd_status,
            "list": self._cmd_list,
            "help": self._cmd_help,
            "settings": self._cmd_settings,
            "config": self._cmd_config
        }
    
    def is_command(self, message_text):
        """
        Check if a message is a bot command
        
        Args:
            message_text (str): The message text to check
            
        Returns:
            bool: True if it's a command, False otherwise
        """
        print(f"DEBUG: is_command called with: '{message_text}'")
        print(f"DEBUG: command_prefix: '{self.command_prefix}'")
        
        if not message_text:
            print(f"DEBUG: message_text is empty or None")
            return False
        
        result = message_text.strip().lower().startswith(self.command_prefix.lower())
        print(f"DEBUG: is_command result: {result}")
        return result
    
    def parse_command(self, message_text):
        """
        Parse a command message and extract the command and arguments
        
        Args:
            message_text (str): The command message
            
        Returns:
            tuple: (command, args) or (None, None) if invalid
        """
        print(f"DEBUG: parse_command called with: '{message_text}'")
        
        if not self.is_command(message_text):
            print(f"DEBUG: Not a command (is_command returned False)")
            return None, None
        
        print(f"DEBUG: Is a command, parsing...")
        
        # Remove the prefix and split into parts
        parts = message_text[len(self.command_prefix):].strip().split()
        print(f"DEBUG: Parts after splitting: {parts}")
        
        if not parts:
            print(f"DEBUG: No parts found after splitting")
            return None, None
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"DEBUG: Parsed command: '{command}', args: {args}")
        return command, args
    
    def execute_command(self, message_text, sender_id, sender_name, group_id, group_name):
        """
        Execute a command from a chat message
        
        Args:
            message_text (str): The command message
            sender_id (str): ID of the message sender
            sender_name (str): Name of the message sender
            group_id (str): ID of the group where command was sent
            group_name (str): Name of the group
            
        Returns:
            str: Response message to send back to the group
        """
        print(f"DEBUG: execute_command called with:")
        print(f"  message_text: '{message_text}'")
        print(f"  sender_id: '{sender_id}'")
        print(f"  sender_name: '{sender_name}'")
        print(f"  group_id: '{group_id}'")
        print(f"  group_name: '{group_name}'")
        print(f"  bot_user_id: '{self.bot_user_id}'")
        
        # Check if this is a duplicate command (same command in same cycle)
        if self.last_processed_command == message_text:
            print(f"DEBUG: Duplicate command detected, ignoring")
            return None
        
        # Check if user is admin for admin-only commands
        command, args = self.parse_command(message_text)
        print(f"DEBUG: Parsed command: '{command}', args: {args}")
        
        if not command:
            print(f"DEBUG: No command found")
            return None
        
        if command not in self.available_commands:
            print(f"DEBUG: Unknown command: '{command}'")
            return f"❌ Unknown command: '{command}'. Type '{self.command_prefix} help' for available commands."
        
        # Check admin status for admin-only commands
        if is_admin_command(command):
            if not self.check_admin_status(sender_id, group_id):
                print(f"DEBUG: User {sender_name} is not admin, command denied")
                return f"❌ Access denied. Only group admins can use the '{command}' command."
        
        try:
            # Execute the command
            print(f"DEBUG: Executing command: '{command}'")
            response = self.available_commands[command](args, sender_id, sender_name, group_id, group_name)
            print(f"DEBUG: Command response: '{response}'")
            
            # Mark this command as processed
            self.last_processed_command = message_text
            
            return response
        except Exception as e:
            print(f"DEBUG: Error executing command: {e}")
            logger.error(f"Error executing command '{command}': {e}")
            return f"❌ Error executing command '{command}': {str(e)}"
    
    def _cmd_activate(self, args, sender_id, sender_name, group_id, group_name):
        """Activate the bot for the current group"""
        if self.commands.is_group_active(group_id):
            return f"✅ Bot is already active for this group ({group_name})"
        
        if self.commands.activate_group(group_id, group_name):
            return f"✅ **SpamShield** activated for {group_name}!\n\nI will now monitor messages and remove spam automatically."
        else:
            return "❌ Failed to activate bot. Please try again or contact an administrator."
    
    def _cmd_deactivate(self, args, sender_id, sender_name, group_id, group_name):
        """Deactivate the bot for the current group"""
        if not self.commands.is_group_active(group_id):
            return f"❌ Bot is not active for this group ({group_name})"
        
        if self.commands.deactivate_group(group_id):
            return f"✅ **SpamShield** deactivated for {group_name}.\n\nI will no longer monitor or remove messages from this group."
        else:
            return "❌ Failed to deactivate bot. Please try again or contact an administrator."
    
    def _cmd_status(self, args, sender_id, sender_name, group_id, group_name):
        """Show the status of the bot for the current group"""
        is_active = self.commands.is_group_active(group_id)
        settings = self.commands.get_group_settings(group_id)
        
        status_text = f"🛡️ **SpamShield Status**\n\n"
        status_text += f"**Group:** {group_name}\n"
        status_text += f"**Status:** {'🟢 Active' if is_active else '🔴 Inactive'}\n"
        
        if is_active:
            status_text += f"**Confidence Threshold:** {settings.get('confidence_threshold', 0.8):.1%}\n"
            status_text += f"**Check Interval:** {settings.get('check_interval', 30)} seconds\n"
            status_text += f"**Model File:** {settings.get('model_file', 'data/training/spam_detection_model.pkl')}\n"
        
        return status_text
    
    def _cmd_list(self, args, sender_id, sender_name, group_id, group_name):
        """List active groups"""
        active_groups = self.commands.get_active_groups()
        
        if not active_groups:
            return "📋 **No active groups**\n\nThe bot is not currently monitoring any groups."
        
        list_text = "📋 **Active Groups**\n\n"
        for i, group in enumerate(active_groups, 1):
            list_text += f"{i}. **{group.get('group_name', 'Unknown')}**\n"
            list_text += f"   ID: `{group['group_id']}`\n"
            list_text += f"   Status: {group.get('status', 'active')}\n"
            list_text += f"   Activated: {group.get('activated_at', 'Unknown')}\n\n"
        
        return list_text
    
    def _cmd_help(self, args, sender_id, sender_name, group_id, group_name):
        """Show help information"""
        help_text = f"🛡️ **SpamShield Commands**\n\n"
        help_text += f"Use these commands with the prefix: `{self.command_prefix}`\n\n"
        
        help_text += "**Available Commands:**\n"
        help_text += "• `activate` - Activate the bot for this group *(Admin only)*\n"
        help_text += "• `deactivate` - Deactivate the bot for this group *(Admin only)*\n"
        help_text += "• `status` - Show bot status for this group\n"
        help_text += "• `help` - Show this help message\n"
        help_text += "• `settings` - Show current settings *(Admin only)*\n"
        help_text += "• `config` - Configure bot behavior *(Admin only)*\n\n"
        
        help_text += "**Examples:**\n"
        help_text += f"• `{self.command_prefix} activate`\n"
        help_text += f"• `{self.command_prefix} status`\n"
        help_text += f"• `{self.command_prefix} deactivate`\n\n"
        
        help_text += "**Note:** Commands marked with *(Admin only)* require group admin privileges."
        
        return help_text
    
    def _cmd_settings(self, args, sender_id, sender_name, group_id, group_name):
        """Show current bot settings"""
        settings = self.commands.get_group_settings(group_id)
        
        settings_text = "⚙️ **Bot Settings**\n\n"
        settings_text += f"**Group:** {group_name}\n"
        settings_text += f"**Confidence Threshold:** {settings.get('confidence_threshold', 0.8):.1%}\n"
        settings_text += f"**Check Interval:** {settings.get('check_interval', 30)} seconds\n"
        settings_text += f"**Model File:** {settings.get('model_file', 'data/training/spam_detection_model.pkl')}\n\n"
        
        settings_text += "**What these mean:**\n"
        settings_text += "• **Confidence Threshold:** How sure the bot must be to remove a message\n"
        settings_text += "• **Check Interval:** How often the bot checks for new messages (seconds)\n"
        settings_text += "• **Model File:** The AI model used for spam detection\n"
        
        return settings_text
    
    def _cmd_config(self, args, sender_id, sender_name, group_id, group_name):
        """Configure bot settings"""
        if not args:
            # Show current config
            global_settings = self.commands.get_global_settings()
            group_settings = self.commands.get_group_settings(group_id)
            
            config_text = "⚙️ **Bot Configuration**\n\n"
            config_text += "**Global Settings:**\n"
            config_text += f"• Show Removal Messages: {'✅ On' if global_settings.get('show_removal_messages', True) else '❌ Off'}\n"
            config_text += f"• Show Startup Message: {'✅ On' if global_settings.get('show_startup_message', True) else '❌ Off'}\n\n"
            
            config_text += "**Group Settings:**\n"
            config_text += f"• Confidence Threshold: {group_settings.get('confidence_threshold', 0.8):.1%}\n"
            config_text += f"• Check Interval: {group_settings.get('check_interval', 30)} seconds\n\n"
            
            config_text += "**Usage:**\n"
            config_text += f"• `{self.command_prefix} config removal on/off` - Toggle removal messages\n"
            config_text += f"• `{self.command_prefix} config startup on/off` - Toggle startup message\n"
            
            return config_text
        
        if len(args) < 2:
            return f"❌ Usage: `{self.command_prefix} config <setting> <on/off>`"
        
        setting = args[0].lower()
        value = args[1].lower()
        
        if value not in ['on', 'off']:
            return f"❌ Value must be 'on' or 'off', got '{value}'"
        
        bool_value = value == 'on'
        
        if setting == 'removal':
            success = self.commands.update_global_settings({'show_removal_messages': bool_value})
            if success:
                status = "✅ On" if bool_value else "❌ Off"
                return f"✅ Removal messages set to {status}"
            else:
                return "❌ Failed to update removal message setting"
        
        elif setting == 'startup':
            success = self.commands.update_global_settings({'show_startup_message': bool_value})
            if success:
                status = "✅ On" if bool_value else "❌ Off"
                return f"✅ Startup message set to {status}"
            else:
                return "❌ Failed to update startup message setting"
        
        else:
            return f"❌ Unknown setting '{setting}'. Use 'removal' or 'startup'"
    
    def check_admin_status(self, sender_id, group_id):
        """
        Check if a user is an admin in a group using GroupMe API
        
        Args:
            sender_id (str): The user ID to check
            group_id (str): The group ID
            
        Returns:
            bool: True if user is admin, False otherwise
        """
        try:
            COMPLETE_URI = f"{BASE_URI}/groups/{group_id}?token={API_KEY}"
            HEADERS = {"Content-Type": "application/json"}
            
            response = requests.get(COMPLETE_URI, headers=HEADERS)
            response.raise_for_status()
            
            response_data = response.json()
            
            if 'response' not in response_data:
                return False
            
            group_data = response_data['response']
            
            # Check if user is in members and is admin
            if 'members' in group_data:
                for member in group_data['members']:
                    if (member.get('user_id') == sender_id and 
                        'admin' in member.get('roles', [])):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

def is_admin_command(command):
    """
    Check if a command requires admin privileges
    
    Args:
        command (str): The command to check
        
    Returns:
        bool: True if admin privileges required
    """
    admin_commands = ['activate', 'deactivate', 'settings', 'config']
    return command in admin_commands


