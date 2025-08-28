"""
Configuration management with validation and defaults.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """Bot configuration with validation."""
    
    # API Configuration
    api_key: str
    bot_user_id: Optional[str] = None
    
    # Model Configuration
    model_file: str = "data/training/spam_detection_model.pkl"
    confidence_threshold: float = 0.8
    
    # Monitoring Configuration
    check_interval: int = 30  # seconds
    max_messages_per_check: int = 100
    
    # Feature Flags
    enable_data_collection: bool = False
    enable_message_deletion: bool = True
    enable_notifications: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = "data/logs/bot.log"
    
    # Data Configuration
    data_dir: str = "data"
    training_dir: str = "data/training"
    logs_dir: str = "data/logs"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
        self._ensure_directories()
    
    def _validate(self):
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("API_KEY is required")
        
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        
        if self.check_interval < 10:
            raise ValueError("check_interval must be at least 10 seconds")
        
        if self.max_messages_per_check < 1:
            raise ValueError("max_messages_per_check must be at least 1")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        Path(self.data_dir).mkdir(exist_ok=True)
        Path(self.training_dir).mkdir(exist_ok=True)
        Path(self.logs_dir).mkdir(exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Create configuration from environment variables."""
        load_dotenv()
        
        return cls(
            api_key=os.getenv("API_KEY", ""),
            bot_user_id=os.getenv("BOT_USER_ID"),
            model_file=os.getenv("MODEL_FILE", "data/training/spam_detection_model.pkl"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.8")),
            check_interval=int(os.getenv("CHECK_INTERVAL", "30")),
            max_messages_per_check=int(os.getenv("MAX_MESSAGES_PER_CHECK", "100")),
            enable_data_collection=os.getenv("ENABLE_DATA_COLLECTION", "false").lower() == "true",
            enable_message_deletion=os.getenv("ENABLE_MESSAGE_DELETION", "true").lower() == "true",
            enable_notifications=os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "data/logs/bot.log"),
        )


@dataclass
class GroupConfig:
    """Configuration for a specific group."""
    
    group_id: str
    group_name: Optional[str] = None
    confidence_threshold: Optional[float] = None
    check_interval: Optional[int] = None
    enabled: bool = True
    
    def __post_init__(self):
        """Validate group configuration."""
        if not self.group_id:
            raise ValueError("group_id is required")


class ConfigManager:
    """Manages bot and group configurations."""
    
    def __init__(self, config_file: str = "data/config/bot_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.bot_config = BotConfig.from_env()
        self.groups: Dict[str, GroupConfig] = {}
        self._load_group_configs()
    
    def _load_group_configs(self):
        """Load group configurations from file."""
        if not self.config_file.exists():
            logger.info(f"Config file {self.config_file} not found, creating default")
            self._save_group_configs()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load group configurations
            groups_data = data.get("groups", {})
            for group_id, group_data in groups_data.items():
                self.groups[group_id] = GroupConfig(
                    group_id=group_id,
                    group_name=group_data.get("name"),
                    confidence_threshold=group_data.get("confidence_threshold"),
                    check_interval=group_data.get("check_interval"),
                    enabled=group_data.get("enabled", True),
                )
            
            logger.info(f"Loaded {len(self.groups)} group configurations")
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            self.groups = {}
    
    def _save_group_configs(self):
        """Save group configurations to file."""
        try:
            data = {
                "groups": {
                    group_id: {
                        "name": group.group_name,
                        "confidence_threshold": group.confidence_threshold,
                        "check_interval": group.check_interval,
                        "enabled": group.enabled,
                    }
                    for group_id, group in self.groups.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.groups)} group configurations")
            
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
    
    def add_group(self, group_config: GroupConfig):
        """Add or update a group configuration."""
        self.groups[group_config.group_id] = group_config
        self._save_group_configs()
        logger.info(f"Added group configuration for {group_config.group_id}")
    
    def remove_group(self, group_id: str):
        """Remove a group configuration."""
        if group_id in self.groups:
            del self.groups[group_id]
            self._save_group_configs()
            logger.info(f"Removed group configuration for {group_id}")
    
    def get_group_config(self, group_id: str) -> Optional[GroupConfig]:
        """Get configuration for a specific group."""
        return self.groups.get(group_id)
    
    def get_enabled_groups(self) -> Dict[str, GroupConfig]:
        """Get all enabled group configurations."""
        return {gid: group for gid, group in self.groups.items() if group.enabled}
    
    def get_group_setting(self, group_id: str, setting: str, default: Any = None) -> Any:
        """Get a specific setting for a group, falling back to bot defaults."""
        group_config = self.get_group_config(group_id)
        
        if group_config and hasattr(group_config, setting):
            value = getattr(group_config, setting)
            if value is not None:
                return value
        
        # Fall back to bot config
        if hasattr(self.bot_config, setting):
            return getattr(self.bot_config, setting)
        
        return default
