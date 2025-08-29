import os
import json
import time
from datetime import datetime, timedelta
import sys
import pickle
import logging
from groupme_bot.bot.chat_commands import ChatCommands

from groupme_bot.ml.model_trainer import predict_spam

# Set up logging
logger = logging.getLogger(__name__)

class SpamMonitor:
    def __init__(self, group_id, api_client=None, config_manager=None, confidence_threshold=0.8, 
                 check_interval=30, dry_run=False):
        """
        Initialize the spam monitor
        
        Args:
            group_id (str): The group ID to monitor
            api_client: GroupMe API client instance
            config_manager: Configuration manager instance
            confidence_threshold (float): Minimum confidence to consider a message spam (0.0-1.0)
            check_interval (int): Interval between checks in seconds
            dry_run (bool): If True, don't actually delete messages
        """
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.check_interval = check_interval
        self.dry_run = dry_run
        self.last_message_id = None
        self.processed_messages = set()
        
        # Use provided API client or create default one
        if api_client:
            self.api_client = api_client
        else:
            from groupme_bot.utils.api_client import create_api_client
            self.api_client = create_api_client()
        
        # Use provided config manager or create default one
        if config_manager:
            self.config_manager = config_manager
        else:
            from groupme_bot.utils.config import ConfigManager
            self.config_manager = ConfigManager()
        
        # Get model file from config
        self.model_file = self.config_manager.bot_config.model_file
        
        # Load the trained model
        self.load_model()
        
        # Initialize chat commands system
        bot_user_id = self.config_manager.bot_config.bot_user_id
        print(f"DEBUG: Initializing chat commands with BOT_USER_ID: '{bot_user_id}'")
        self.chat_commands = ChatCommands(bot_user_id)
        
        # Check if user is admin in the group (for sending messages)
        if not self.check_admin_status():
            logger.warning(f"Bot user is not an admin in group {group_id}. Some features may be limited.")
    
    def load_model(self):
        """Load the trained spam detection model"""
        try:
            # Try to load the new model format first (separate model and vectorizer files)
            model_file = 'data/training/spam_detection_model.pkl'
            vectorizer_file = 'data/training/tfidf_vectorizer.pkl'
            
            if os.path.exists(model_file) and os.path.exists(vectorizer_file):
                # Load new format (separate files)
                with open(model_file, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                
                self.model_name = type(self.model).__name__
                self.model_accuracy = 0.975  # From our recent training
                
                logger.info(f"Loaded new model: {self.model_name} (Accuracy: {self.model_accuracy:.4f})")
                
            else:
                # Try to load old format (single file with dictionary)
                with open(self.model_file, 'rb') as f:
                    self.model_data = pickle.load(f)
                
                self.model = self.model_data['model']
                self.vectorizer = self.model_data['vectorizer']
                self.model_name = self.model_data['model_name']
                self.model_accuracy = self.model_data['accuracy']
                
                logger.info(f"Loaded old model: {self.model_name} (Accuracy: {self.model_accuracy:.4f})")
            
        except FileNotFoundError:
            logger.error(f"Model files not found. Please train the model first.")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def check_admin_status(self):
        """Check if the bot user is an admin in the group"""
        try:
            group_data = self.api_client.get_group(self.group_id)
            
            if not group_data:
                return False
            
            # Check if bot user is in members and is admin
            bot_user_id = self.config_manager.bot_config.bot_user_id
            if 'members' in group_data and bot_user_id:
                for member in group_data['members']:
                    if (member.get('user_id') == bot_user_id and 
                        'admin' in member.get('roles', [])):
                        logger.info(f"Bot user is admin in group {self.group_id}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    

    
    def get_recent_messages(self, limit=20):
        """Get recent messages from the group"""
        try:
            messages = self.api_client.get_messages(self.group_id, limit=limit)
            
            if not messages:
                return []
            
            # Filter out system messages and non-text messages
            real_messages = []
            for message in messages:
                sender_name = message.get('name', 'Unknown')
                user_id = message.get('user_id', '')
                text = message.get('text', '')
                
                # Skip system messages and messages without text
                if (sender_name == 'GroupMe' or 
                    not user_id or 
                    not text or  # Skip messages without text (images, attachments, etc.)
                    (text and 'has joined the group' in text) or
                    (text and 'has left the group' in text) or
                    (text and 'has been removed from the group' in text) or
                    (text and 'has been added to the group' in text) or
                    (text and 'This message was deleted' in text) or
                    (text and 'This message was removed' in text) or
                    (text and 'An admin deleted this message' in text)):
                    continue
                
                real_messages.append(message)
            
            return real_messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def detect_spam(self, message):
        """Detect if a message is spam using the trained model"""
        try:
            text = message.get('text', '')
            attachments = message.get('attachments', [])
            
            # If message has no text and only has attachments, skip spam detection
            if not text and attachments:
                return False, 0.0
            
            # If no text at all, skip spam detection
            if not text:
                return False, 0.0
            
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Transform text using vectorizer
            features = self.vectorizer.transform([processed_text])
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            # Get confidence for the predicted class
            if prediction == 'spam':
                confidence = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                confidence = probabilities[0]
            
            is_spam = prediction == 'spam' and confidence >= self.confidence_threshold
            
            return is_spam, confidence
            
        except Exception as e:
            logger.error(f"Error detecting spam: {e}")
            return False, 0.0
    
    def preprocess_text(self, text):
        """Preprocess text for prediction"""
        import re
        
        if not text or text == '':
            return ''
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def can_remove_message(self, message):
        """
        Check if a message can be removed based on various criteria
        
        Args:
            message (dict): The message object
            
        Returns:
            tuple: (can_remove, reason)
        """
        try:
            # Check if message is too old (GroupMe has limits on message deletion)
            created_at = message.get('created_at', 0)
            if created_at:
                message_age = time.time() - created_at
                # GroupMe typically doesn't allow deletion of messages older than 24 hours
                if message_age > 86400:  # 24 hours in seconds
                    return False, "Message is too old to delete"
            
            # Check if message has attachments (some attachments can't be deleted)
            attachments = message.get('attachments', [])
            if attachments:
                attachment_types = [att.get('type', 'unknown') for att in attachments]
                for attachment in attachments:
                    if attachment.get('type') in ['image', 'video', 'file']:
                        return False, f"Message contains {attachment.get('type')} attachment that cannot be deleted"
                # If we get here, attachments are allowed (like emoji, mentions, etc.)
                logger.info(f"Message has allowed attachments: {', '.join(attachment_types)}")
            
            # Check if message is from the bot itself (usually can't delete own messages)
            user_id = message.get('user_id', '')
            if user_id == BOT_USER_ID:
                return False, "Cannot delete bot's own messages"
            
            return True, "Message can be removed"
            
        except Exception as e:
            logger.error(f"Error checking if message can be removed: {e}")
            return False, f"Error checking message: {e}"

    def send_spam_notification(self, message, confidence):
        """
        Send a notification message to the group about detected spam
        
        Args:
            message (dict): The spam message that was detected
            confidence (float): Confidence score of the spam detection
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            sender_name = message.get('name', 'Unknown')
            text = message.get('text', '')
            
            # Handle messages without text
            if not text:
                text = "[No text content]"
            
            # Truncate long messages
            display_text = text[:100]
            
            # Create notification message
            notification_text = f"🚨 SPAM DETECTED 🚨\n\nFrom: {sender_name}\nMessage: \"{display_text}{'...' if len(text) > 100 else ''}\"\nConfidence: {confidence:.1%}\n\nThis message has been flagged as potential spam by our AI detection system."
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send notification: {notification_text}")
                return True
            
            response = self.api_client.send_message(
                self.group_id, 
                notification_text,
                source_guid=str(int(time.time() * 1000))
            )
            
            logger.info(f"Sent spam notification for message from {sender_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending spam notification: {e}")
            return False
    
    def delete_message(self, message_id):
        """
        Delete a message using the GroupMe API
        
        Args:
            message_id (str): The message ID to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would delete message {message_id}")
                return True
            
            success = self.api_client.delete_message(self.group_id, message_id)
            
            if success:
                logger.info(f"Successfully deleted message {message_id}")
            else:
                logger.error(f"Failed to delete message {message_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            return False
    
    def send_spam_removed_notification(self, sender_name):
        """
        Send a simple one-line notification that spam was removed
        
        Args:
            sender_name (str): Name of the spam sender
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        # Check if removal messages are enabled
        global_settings = self.chat_commands.commands.get_global_settings()
        if not global_settings.get('show_removal_messages', True):
            logger.info("Removal messages disabled, skipping notification")
            return True
        
        try:
            notification_text = f"ANTI-SPAM-BOT: Spam message from {sender_name} has been removed."
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send removal notification: {notification_text}")
                return True
            
            response = self.api_client.send_message(
                self.group_id,
                notification_text,
                source_guid=str(int(time.time() * 1000))
            )
            
            logger.info(f"Sent spam removed notification for {sender_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending spam removed notification: {e}")
            return False
    
    def send_spam_notification_simple(self, sender_name, confidence, message_id):
        """
        Send a simple spam notification as a reply to the specific message
        
        Args:
            sender_name (str): Name of the spam sender
            confidence (float): Confidence score
            message_id (str): ID of the message to reply to
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            notification_text = f"ANTI-SPAM-BOT: SPAM MESSAGE DETECTED\n\nUser: {sender_name}\nConfidence: {confidence:.1%}\n\n"
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send notification reply: {notification_text}")
                return True
            
            response = self.api_client.send_message(
                self.group_id,
                notification_text,
                source_guid=str(int(time.time() * 1000))
            )
            
            logger.info(f"Sent spam notification reply to message {message_id} from {sender_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending spam notification reply: {e}")
            return False
    
    def process_messages(self):
        """Process recent messages and remove spam"""
        # Reset the last processed command at the start of each cycle
        self.chat_commands.last_processed_command = None
        
        messages = self.get_recent_messages(limit=20)
        
        if not messages:
            print("No messages found in this check cycle")
            return
        
        print(f"Found {len(messages)} messages to check")
        
        # Update last message ID for tracking
        if not self.last_message_id:
            self.last_message_id = messages[0]['id']
            print(f"Starting to track from message ID: {self.last_message_id}")
        
        spam_removed = 0
        new_messages_checked = 0
        
        for message in messages:
            message_id = message['id']
            
            # Skip if already processed
            if message_id in self.processed_messages:
                continue
            
            # Skip if this is an older message (already processed)
            if message_id == self.last_message_id:
                break
            
            # This is a new message to check
            new_messages_checked += 1
            sender_name = message.get('name', 'Unknown')
            sender_id = message.get('user_id', '')
            text = message.get('text', '')
            attachments = message.get('attachments', [])
            
            # Handle messages with attachments (images, etc.)
            if attachments:
                attachment_types = [att.get('type', 'unknown') for att in attachments]
                print(f"Checking message from {sender_name}: [Message with attachments: {', '.join(attachment_types)}]")
                if text:
                    print(f"  -> Text content: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            else:
                print(f"Checking message from {sender_name}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Check if this is a command
            if self.chat_commands.is_command(text):
                print(f"  -> COMMAND DETECTED from {sender_name}")
                print(f"  -> Command text: '{text}'")
                response = self.chat_commands.execute_command(text, sender_id, sender_name, self.group_id, "Current Group")
                print(f"  -> Command response: {response}")
                if response:
                    print(f"  -> Sending response to group...")
                    success = self.send_message(response)
                    print(f"  -> Response sent successfully: {success}")
                else:
                    print(f"  -> No response to send")
                self.processed_messages.add(message_id)
                continue
            
            # Detect spam
            is_spam, confidence = self.detect_spam(message)
            
            print(f"  -> Prediction: {'SPAM' if is_spam else 'Regular'} (Confidence: {confidence:.3f})")
            
            if is_spam:
                if attachments:
                    attachment_types = [att.get('type', 'unknown') for att in attachments]
                    logger.info(f"SPAM DETECTED: {sender_name} - '{text}...' [with attachments: {', '.join(attachment_types)}] (Confidence: {confidence:.3f})")
                else:
                    logger.info(f"SPAM DETECTED: {sender_name} - '{text}...' (Confidence: {confidence:.3f})")
                
                # Try to delete the spam message first
                if self.delete_message(message_id):
                    spam_removed += 1
                    logger.info(f"Deleted spam message from {sender_name}")
                    print(f"  -> DELETED spam message from {sender_name}")
                    # Send simple notification that spam was removed
                    self.send_spam_removed_notification(sender_name)
                else:
                    # If deletion fails, send notification as fallback
                    if self.send_spam_notification_simple(sender_name, confidence, message_id):
                        spam_removed += 1
                        logger.info(f"Sent spam notification reply for {sender_name} (deletion failed)")
                        print(f"  -> SENT SPAM NOTIFICATION REPLY for {sender_name} (deletion failed)")
                    else:
                        logger.error(f"Failed to delete or notify about spam from {sender_name}")
                        print(f"  -> FAILED to handle spam from {sender_name}")
            else:
                print(f"  -> Keeping regular message from {sender_name}")
            
            # Mark as processed
            self.processed_messages.add(message_id)
        
        if new_messages_checked > 0:
            print(f"Checked {new_messages_checked} new messages in this cycle")
        else:
            print("No new messages to check in this cycle")
        
        if spam_removed > 0:
            logger.info(f"Removed {spam_removed} spam messages in this cycle")
            print(f"Removed {spam_removed} spam messages in this cycle")
        
        # Update last message ID
        if messages:
            self.last_message_id = messages[0]['id']
    
    def send_startup_message(self):
        """
        Send a startup message to alert the group that the anti-spam bot is active
        """
        # Check if startup message is enabled
        global_settings = self.chat_commands.commands.get_global_settings()
        if not global_settings.get('show_startup_message', True):
            logger.info("Startup message disabled, skipping")
            print("Startup message disabled, skipping")
            return True
        
        try:
            startup_text = f"🤖 **ANTI-SPAM BOT ACTIVATED**\n\nI'm now monitoring this group for spam messages and will automatically remove them.\n\n**Commands:**\n• `/spam-bot: help` - Show all available commands\n• `/spam-bot: status` - Check bot status\n• `/spam-bot: activate` - Activate bot for this group\n• `/spam-bot: deactivate` - Deactivate bot for this group"
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send startup message: {startup_text}")
                return True
            
            response = self.api_client.send_message(
                self.group_id,
                startup_text,
                source_guid=str(int(time.time() * 1000))
            )
            
            logger.info(f"Sent startup message to group {self.group_id}")
            print(f"Sent startup message to group {self.group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
            print(f"Failed to send startup message: {e}")
            return False
    
    def run_monitor(self, check_interval=None):
        """
        Run the spam monitor continuously
        
        Args:
            check_interval (int): How often to check for new messages (seconds). 
                                 If None, uses the value from bot configuration.
        """
        # Use configured check_interval if not provided
        if check_interval is None:
            check_interval = self.check_interval
        
        logger.info(f"Starting spam monitor for group {self.group_id}")
        logger.info(f"Confidence threshold: {self.confidence_threshold}")
        logger.info(f"Check interval: {check_interval} seconds")
        
        # Send startup message to alert the group
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sending startup message to group...")
        self.send_startup_message()
        
        # Initial check of existing messages
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Performing initial check of last 20 existing messages...")
        self.process_existing_messages(limit=20)
        
        try:
            while True:
                try:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new messages...")
                    self.process_messages()
                    print(f"Waiting {check_interval} seconds until next check...")
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Spam monitor stopped by user")
                    print("\nSpam monitor stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in monitor loop: {e}")
                    print(f"Error in monitor loop: {e}")
                    time.sleep(check_interval)
                    
        except Exception as e:
            logger.error(f"Fatal error in spam monitor: {e}")
    
    def process_existing_messages(self, limit=20):
        """
        Process existing messages without tracking for new ones
        
        Args:
            limit (int): Number of recent messages to check
        """
        messages = self.get_recent_messages(limit=limit)
        
        if not messages:
            print("No existing messages found to check")
            return
        
        print(f"Found {len(messages)} existing messages to check")
        
        spam_removed = 0
        messages_checked = 0
        
        for message in messages:
            message_id = message['id']
            sender_name = message.get('name', 'Unknown')
            text = message.get('text', '')
            attachments = message.get('attachments', [])
            
            # Handle messages with attachments (images, etc.)
            if attachments:
                attachment_types = [att.get('type', 'unknown') for att in attachments]
                print(f"Checking existing message from {sender_name}: [Message with attachments: {', '.join(attachment_types)}]")
                if text:
                    print(f"  -> Text content: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            else:
                print(f"Checking existing message from {sender_name}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Detect spam
            is_spam, confidence = self.detect_spam(message)
            
            print(f"  -> Prediction: {'SPAM' if is_spam else 'Regular'} (Confidence: {confidence:.3f})")
            
            if is_spam:
                if attachments:
                    attachment_types = [att.get('type', 'unknown') for att in attachments]
                    logger.info(f"EXISTING SPAM DETECTED: {sender_name} - '{text}...' [with attachments: {', '.join(attachment_types)}] (Confidence: {confidence:.3f})")
                else:
                    logger.info(f"EXISTING SPAM DETECTED: {sender_name} - '{text}...' (Confidence: {confidence:.3f})")
                
                # Try to delete the spam message first
                if self.delete_message(message_id):
                    spam_removed += 1
                    logger.info(f"Deleted existing spam message from {sender_name}")
                    print(f"  -> DELETED existing spam message from {sender_name}")
                    # Send simple notification that spam was removed
                    self.send_spam_removed_notification(sender_name)
                else:
                    # If deletion fails, send notification as fallback
                    if self.send_spam_notification_simple(sender_name, confidence, message_id):
                        spam_removed += 1
                        logger.info(f"Sent spam notification reply for existing message from {sender_name} (deletion failed)")
                        print(f"  -> SENT SPAM NOTIFICATION REPLY for existing message from {sender_name} (deletion failed)")
                    else:
                        logger.error(f"Failed to delete or notify about existing spam from {sender_name}")
                        print(f"  -> FAILED to handle existing spam from {sender_name}")
            else:
                print(f"  -> Keeping existing regular message from {sender_name}")
            
            messages_checked += 1
            # Mark as processed so it won't be checked again
            self.processed_messages.add(message_id)
        
        print(f"Checked {messages_checked} existing messages")
        if spam_removed > 0:
            logger.info(f"Removed {spam_removed} existing spam messages")
            print(f"Removed {spam_removed} existing spam messages")
        
        # Set the last message ID to the most recent message
        if messages:
            self.last_message_id = messages[0]['id']
            print(f"Now tracking from message ID: {self.last_message_id}")
    
    def send_message(self, text):
        """
        Send a message to the group
        
        Args:
            text (str): The message text to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send message: {text}")
                return True
            
            response = self.api_client.send_message(
                self.group_id,
                text,
                source_guid=str(int(time.time() * 1000))
            )
            
            logger.info(f"Sent message to group {self.group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

def main():
    """Main function to run the spam monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GroupMe Spam Monitor')
    parser.add_argument('--group-id', required=True, help='Group ID to monitor')
    parser.add_argument('--confidence', type=float, default=0.8, help='Confidence threshold (0.0-1.0)')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    
    args = parser.parse_args()
    
    try:
        monitor = SpamMonitor(
            group_id=args.group_id,
            confidence_threshold=args.confidence,
            check_interval=args.interval,
            dry_run=args.dry_run
        )
        
        monitor.run_monitor(check_interval=args.interval)
        
    except Exception as e:
        logger.error(f"Failed to start spam monitor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
