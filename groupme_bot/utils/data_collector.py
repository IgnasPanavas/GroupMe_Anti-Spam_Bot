"""
Data collection utility for gathering messages from multiple groups.
"""

import os
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from groupme_bot.utils.api_client import create_api_client

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects messages from GroupMe groups and saves them to CSV files."""
    
    def __init__(self, output_dir: str = "data/raw_messages"):
        self.api_client = create_api_client()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_group_name_safe(self, group_name: str) -> str:
        """Convert group name to a safe filename."""
        # Remove or replace characters that aren't safe for filenames
        safe_name = "".join(c for c in group_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        return safe_name
    
    def collect_from_group(self, group_id: str, limit: int = 100, save_attachments: bool = False) -> str:
        """
        Collect messages from a specific group.
        
        Args:
            group_id: The GroupMe group ID
            limit: Maximum number of messages to collect
            save_attachments: Whether to include attachment info in the CSV
            
        Returns:
            Path to the created CSV file
        """
        try:
            # Get group info
            group_info = self.api_client.get_group(group_id)
            if not group_info:
                logger.error(f"Group {group_id} not found or not accessible")
                return None
            
            group_name = group_info.get('name', f'group_{group_id}')
            safe_group_name = self.get_group_name_safe(group_name)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_group_name}_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            logger.info(f"Collecting {limit} messages from group: {group_name}")
            
            # Collect messages with pagination if needed
            messages = []
            remaining_limit = limit
            before_id = None
            
            while remaining_limit > 0:
                batch_limit = min(remaining_limit, 100)  # GroupMe API limit per request
                batch_messages = self.api_client.get_messages(group_id, limit=batch_limit, before_id=before_id)
                
                if not batch_messages:
                    break
                
                messages.extend(batch_messages)
                remaining_limit -= len(batch_messages)
                
                # Get the oldest message ID for next batch
                if batch_messages:
                    before_id = batch_messages[-1]['id']
                
                # Small delay to be respectful to the API
                time.sleep(0.5)
            
            if not messages:
                logger.warning(f"No messages found in group {group_name}")
                return None
            
            # Filter and process messages
            processed_messages = []
            for message in messages:
                processed_msg = self._process_message(message, save_attachments)
                if processed_msg:
                    processed_messages.append(processed_msg)
            
            # Save to CSV
            self._save_to_csv(processed_messages, filepath, save_attachments)
            
            logger.info(f"Saved {len(processed_messages)} messages to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error collecting from group {group_id}: {e}")
            return None
    
    def collect_from_multiple_groups(self, group_ids: List[str], limit_per_group: int = 100) -> Dict[str, str]:
        """
        Collect messages from multiple groups.
        
        Args:
            group_ids: List of GroupMe group IDs
            limit_per_group: Maximum messages per group
            
        Returns:
            Dictionary mapping group_id to CSV filepath
        """
        results = {}
        
        for group_id in group_ids:
            logger.info(f"Collecting from group {group_id}...")
            filepath = self.collect_from_group(group_id, limit_per_group)
            if filepath:
                results[group_id] = filepath
            else:
                logger.error(f"Failed to collect from group {group_id}")
            
            # Small delay to be respectful to the API
            time.sleep(1)
        
        return results
    
    def _process_message(self, message: Dict[str, Any], save_attachments: bool = False) -> Optional[Dict[str, Any]]:
        """Process a single message for CSV output."""
        try:
            # Skip system messages
            sender_name = message.get('name', '')
            if sender_name == 'GroupMe':
                return None
            
            # Skip messages without text
            text = message.get('text', '').strip()
            if not text:
                return None
            
            # Skip system messages
            if any(phrase in text.lower() for phrase in [
                'has joined the group', 'has left the group', 'has been removed',
                'has been added', 'this message was deleted', 'this message was removed',
                'an admin deleted this message'
            ]):
                return None
            
            # Clean the text - replace newlines and extra whitespace
            text = text.replace('\n', ' ').replace('\r', ' ')
            text = ' '.join(text.split())  # Normalize whitespace
            
            processed = {
                'text': text,
                'label': 'ham'  # Default to ham (non-spam), change to spam when found
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def _save_to_csv(self, messages: List[Dict[str, Any]], filepath: Path, save_attachments: bool = False):
        """Save messages to CSV file."""
        if not messages:
            return
        
        fieldnames = ['text', 'label']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for message in messages:
                writer.writerow(message)
    
    def list_available_groups(self) -> List[Dict[str, Any]]:
        """List all groups the bot has access to."""
        try:
            groups = self.api_client.get_groups()
            return groups
        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            return []
    
    def create_labeling_template(self, csv_filepath: str) -> str:
        """
        Create a template for manual labeling.
        
        Args:
            csv_filepath: Path to the CSV file to create template for
            
        Returns:
            Path to the labeling template
        """
        template_path = Path(csv_filepath).with_suffix('.template.csv')
        
        # Copy the original file and add labeling instructions
        with open(csv_filepath, 'r', encoding='utf-8') as infile:
            content = infile.read()
        
        # Add header with instructions
        instructions = """# LABELING INSTRUCTIONS
# 
# For each message, set the 'label' field to one of:
# - 'spam': Messages that are unwanted, promotional, or inappropriate
# - 'regular': Normal conversation messages
# - 'questionable': Messages you're unsure about (optional)
#
# You can also add notes in the 'notes' field for any observations.
#
# Examples of spam:
# - "Selling tickets", "Buy now", "Click here", "Free money"
# - Promotional messages, scams, unwanted solicitations
#
# Examples of regular:
# - "Hey everyone", "What time is the meeting?", "Thanks!"
# - Normal conversation, questions, responses
#
"""
        
        with open(template_path, 'w', encoding='utf-8') as outfile:
            outfile.write(instructions)
            outfile.write(content)
        
        logger.info(f"Created labeling template: {template_path}")
        return str(template_path)


def main():
    """Command-line interface for data collection."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GroupMe Data Collector')
    parser.add_argument('--group-id', help='Single group ID to collect from')
    parser.add_argument('--group-ids', nargs='+', help='Multiple group IDs to collect from')
    parser.add_argument('--limit', type=int, default=1000, help='Maximum messages per group')
    parser.add_argument('--output-dir', default='data/raw_messages', help='Output directory')
    parser.add_argument('--save-attachments', action='store_true', help='Include attachment info')
    parser.add_argument('--list-groups', action='store_true', help='List available groups')
    parser.add_argument('--create-template', help='Create labeling template for CSV file')
    
    args = parser.parse_args()
    
    collector = DataCollector(args.output_dir)
    
    if args.list_groups:
        print("Available groups:")
        groups = collector.list_available_groups()
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group.get('name', 'Unknown')} (ID: {group.get('group_id')})")
        return
    
    if args.create_template:
        template_path = collector.create_labeling_template(args.create_template)
        print(f"Template created: {template_path}")
        return
    
    if args.group_id:
        filepath = collector.collect_from_group(args.group_id, args.limit, args.save_attachments)
        if filepath:
            print(f"Data collected: {filepath}")
        else:
            print("Failed to collect data")
    
    elif args.group_ids:
        results = collector.collect_from_multiple_groups(args.group_ids, args.limit)
        print(f"Collected from {len(results)} groups:")
        for group_id, filepath in results.items():
            print(f"  {group_id}: {filepath}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
