"""
Command-line interface for the GroupMe Anti-Spam Bot.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from groupme_bot.utils.config import ConfigManager, GroupConfig
from groupme_bot.utils.api_client import create_api_client
from groupme_bot.bot.spam_monitor import SpamMonitor


def setup_logging(config_manager) -> None:
    """Setup structured logging."""
    log_config = config_manager.bot_config
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_config.log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_config.log_file:
        file_handler = logging.FileHandler(log_config.log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def resolve_group_id(group_identifier, api_client):
    """Resolve group name or ID to group ID."""
    try:
        # Try to parse as integer (group ID)
        group_id = int(group_identifier)
        return str(group_id)
    except ValueError:
        # Not an integer, treat as group name
        groups = api_client.get_groups()
        
        # Find group by name (case-insensitive)
        for group in groups:
            if group.get('name', '').lower() == group_identifier.lower():
                return str(group.get('group_id'))
        
        # If exact match not found, try partial match
        for group in groups:
            if group_identifier.lower() in group.get('name', '').lower():
                return str(group.get('group_id'))
        
        raise ValueError(f"Group '{group_identifier}' not found")

def start_bot(args) -> int:
    """Start the spam monitoring bot."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        setup_logging(config_manager)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting SpamShield")
        
        # Validate group identifier
        if not args.group_id:
            logger.error("Group ID or name is required")
            return 1
        
        # Create API client
        api_client = create_api_client()
        
        # Resolve group identifier to group ID
        try:
            resolved_group_id = resolve_group_id(args.group_id, api_client)
            logger.info(f"Resolved '{args.group_id}' to group ID: {resolved_group_id}")
        except ValueError as e:
            logger.error(f"Group resolution failed: {e}")
            return 1
        
        # Test API connection
        group_info = api_client.get_group(resolved_group_id)
        if not group_info:
            logger.error(f"Group {resolved_group_id} not found or not accessible")
            return 1
        
        logger.info(f"Connected to group: {group_info.get('name', 'Unknown')}")
        
        # Get check interval from config if not specified via command line
        check_interval = args.interval
        if check_interval is None or check_interval == 30:  # Default value
            # Try to get from JSON config file
            try:
                config_file = "data/config/bot_config.json"
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    config_interval = config_data.get("settings", {}).get("check_interval")
                    if config_interval:
                        check_interval = config_interval
                        logger.info(f"Using check interval from config file: {check_interval} seconds")
            except Exception as e:
                logger.warning(f"Could not read check interval from config file: {e}")
        
        # Create spam monitor
        monitor = SpamMonitor(
            group_id=resolved_group_id,
            api_client=api_client,
            config_manager=config_manager,
            confidence_threshold=args.confidence,
            check_interval=check_interval,
            dry_run=args.dry_run,
        )
        
        # Start monitoring
        monitor.run_monitor()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        return 1


def train_model(args) -> int:
    """Train the spam detection model."""
    try:
        from groupme_bot.ml.model_trainer import main as train_main
        
        logger = logging.getLogger(__name__)
        logger.info("Starting model training")
        
        train_main()
        
        logger.info("Model training completed")
        return 0
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return 1


def collect_data(args) -> int:
    """Collect training data from groups."""
    try:
        from groupme_bot.utils.groupme_api import get_messages_and_save_to_training
        
        logger = logging.getLogger(__name__)
        logger.info(f"Collecting data from group {args.group_id}")
        
        get_messages_and_save_to_training(
            group_id=args.group_id,
            limit=args.limit,
            label=args.label,
        )
        
        logger.info("Data collection completed")
        return 0
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        return 1


def handle_data_commands(args) -> int:
    """Handle data collection and preparation commands."""
    try:
        from groupme_bot.utils.data_collector import DataCollector
        from groupme_bot.utils.data_preparer import DataPreparer
        
        if args.list_groups:
            collector = DataCollector()
            groups = collector.list_available_groups()
            
            print(f"\nFound {len(groups)} groups:")
            print("=" * 60)
            
            for i, group in enumerate(groups, 1):
                print(f"{i}. {group.get('name', 'Unknown')}")
                print(f"   ID: {group.get('group_id')}")
                print(f"   Members: {group.get('members_count', 'Unknown')}")
                if group.get('description'):
                    print(f"   Description: {group['description']}")
                print()
            
            return 0
        
        if args.collect_from:
            collector = DataCollector()
            results = collector.collect_from_multiple_groups(args.collect_from, args.limit)
            
            print(f"\nCollected from {len(results)} groups:")
            for group_id, filepath in results.items():
                print(f"  {group_id}: {filepath}")
            
            return 0
        
        if args.validate:
            preparer = DataPreparer()
            preparer.validate_labels(args.validate)
            return 0
        
        if args.combine:
            preparer = DataPreparer()
            output_file = preparer.combine_labeled_data()
            
            if output_file and args.create_splits:
                preparer.create_training_splits(output_file)
            
            return 0
        
        if args.create_splits:
            preparer = DataPreparer()
            preparer.create_training_splits("data/training/combined_labeled_data.csv")
            return 0
        
        print("No action specified. Use --help for options.")
        return 1
        
    except Exception as e:
        logger.error(f"Data command failed: {e}")
        return 1


def list_groups(args) -> int:
    """List available groups."""
    try:
        api_client = create_api_client()
        groups = api_client.get_groups()
        
        print(f"\nFound {len(groups)} groups:")
        print("=" * 60)
        
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group.get('name', 'Unknown')}")
            print(f"   ID: {group.get('group_id')}")
            print(f"   Members: {group.get('members_count', 'Unknown')}")
            if group.get('description'):
                print(f"   Description: {group['description']}")
            print()
        
        return 0
        
    except Exception as e:
        print(f"Error listing groups: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SpamShield - GroupMe Anti-Spam Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  groupme-bot start --group-id 123456789
  groupme-bot start --group-id "Anti-spam-bot-test-group"
  groupme-bot start --group-id 123456789 --confidence 0.9 --interval 60
  groupme-bot train
  groupme-bot collect --group-id 123456789 --limit 100
  groupme-bot data --collect-from 123456789 987654321 --limit 500
  groupme-bot data --combine --create-splits
  groupme-bot groups
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the spam monitoring bot')
    start_parser.add_argument('--group-id', required=True, help='Group ID or name to monitor')
    start_parser.add_argument('--confidence', type=float, default=0.8, 
                             help='Confidence threshold (0.0-1.0)')
    start_parser.add_argument('--interval', type=int, default=30,
                             help='Check interval in seconds')
    start_parser.add_argument('--dry-run', action='store_true',
                             help='Run without making changes')
    start_parser.set_defaults(func=start_bot)
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the spam detection model')
    train_parser.set_defaults(func=train_model)
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect training data')
    collect_parser.add_argument('--group-id', required=True, help='Group ID to collect from')
    collect_parser.add_argument('--limit', type=int, default=300, help='Number of messages to collect')
    collect_parser.add_argument('--label', choices=['regular', 'spam'], default='regular',
                               help='Label for collected messages')
    collect_parser.set_defaults(func=collect_data)
    
    # Data collection command
    data_parser = subparsers.add_parser('data', help='Advanced data collection and preparation')
    data_parser.add_argument('--collect-from', nargs='+', help='Group IDs to collect messages from')
    data_parser.add_argument('--limit', type=int, default=100, help='Messages per group')
    data_parser.add_argument('--combine', action='store_true', help='Combine labeled CSV files')
    data_parser.add_argument('--create-splits', action='store_true', help='Create training/testing splits')
    data_parser.add_argument('--validate', help='Validate labels in a CSV file')
    data_parser.add_argument('--list-groups', action='store_true', help='List available groups')
    data_parser.set_defaults(func=handle_data_commands)
    
    # Groups command
    groups_parser = subparsers.add_parser('groups', help='List available groups')
    groups_parser.set_defaults(func=list_groups)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
