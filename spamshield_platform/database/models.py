"""
Database models for SpamShield Platform
SQLAlchemy models for PostgreSQL database
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Text, 
    DECIMAL, ARRAY, JSON, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Group(Base):
    """Monitored GroupMe groups"""
    __tablename__ = 'groups'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), unique=True, nullable=False)
    group_name = Column(String(255), nullable=False)
    status = Column(String(20), default='active')
    owner_id = Column(String(50))
    owner_name = Column(String(255))
    member_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True))
    last_message_id = Column(String(50))
    error_count = Column(Integer, default=0)
    error_message = Column(Text)
    group_metadata = Column(JSONB, default={})
    
    # Relationships
    config = relationship("GroupConfig", back_populates="group", uselist=False)
    assignments = relationship("GroupAssignment", back_populates="group")
    message_logs = relationship("MessageLog", back_populates="group")
    daily_stats = relationship("DailyStat", back_populates="group")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'paused', 'error')"),
        Index('idx_groups_group_id', 'group_id'),
        Index('idx_groups_status', 'status'),
        Index('idx_groups_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<Group(group_id='{self.group_id}', name='{self.group_name}', status='{self.status}')>"

class GroupConfig(Base):
    """Configuration settings for each group"""
    __tablename__ = 'group_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), ForeignKey('groups.group_id', ondelete='CASCADE'), unique=True)
    
    # Spam detection settings
    confidence_threshold = Column(DECIMAL(3,2), default=0.80)
    check_interval_seconds = Column(Integer, default=30)
    
    # Action settings
    auto_delete_spam = Column(Boolean, default=True)
    notify_on_removal = Column(Boolean, default=True)
    notify_admins = Column(Boolean, default=True)
    send_startup_message = Column(Boolean, default=True)
    
    # Advanced settings
    max_message_age_hours = Column(Integer, default=24)
    batch_size = Column(Integer, default=20)
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Model settings
    model_version = Column(String(50), default='latest')
    custom_keywords = Column(ARRAY(Text))
    whitelist_users = Column(ARRAY(Text))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="config")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("confidence_threshold BETWEEN 0.0 AND 1.0"),
        CheckConstraint("check_interval_seconds BETWEEN 5 AND 3600"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for easy serialization"""
        return {
            'confidence_threshold': float(self.confidence_threshold),
            'check_interval_seconds': self.check_interval_seconds,
            'auto_delete_spam': self.auto_delete_spam,
            'notify_on_removal': self.notify_on_removal,
            'notify_admins': self.notify_admins,
            'send_startup_message': self.send_startup_message,
            'max_message_age_hours': self.max_message_age_hours,
            'batch_size': self.batch_size,
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'model_version': self.model_version,
            'custom_keywords': self.custom_keywords or [],
            'whitelist_users': self.whitelist_users or [],
        }

class BotInstance(Base):
    """Bot instance tracking and management"""
    __tablename__ = 'bot_instances'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_name = Column(String(100), unique=True, nullable=False)
    hostname = Column(String(255))
    process_id = Column(Integer)
    status = Column(String(20), default='starting')
    
    # Capacity and load
    max_groups = Column(Integer, default=10)
    current_groups = Column(Integer, default=0)
    cpu_usage = Column(DECIMAL(5,2))
    memory_usage_mb = Column(Integer)
    
    # Health tracking
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(String(20))
    
    # Assigned groups
    assigned_groups = Column(ARRAY(Text))
    
    # Relationships
    assignments = relationship("GroupAssignment", back_populates="instance")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('starting', 'running', 'stopping', 'stopped', 'error')"),
    )
    
    @property
    def is_healthy(self) -> bool:
        """Check if instance is healthy based on heartbeat"""
        if not self.last_heartbeat:
            return False
        time_diff = datetime.utcnow() - self.last_heartbeat.replace(tzinfo=None)
        return time_diff.total_seconds() < 300  # 5 minutes

class GroupAssignment(Base):
    """Assignment of groups to bot instances"""
    __tablename__ = 'group_assignments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), ForeignKey('groups.group_id', ondelete='CASCADE'))
    instance_id = Column(UUID(as_uuid=True), ForeignKey('bot_instances.id', ondelete='CASCADE'))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='active')
    
    # Relationships
    group = relationship("Group", back_populates="assignments")
    instance = relationship("BotInstance", back_populates="assignments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'reassigning')"),
        UniqueConstraint('group_id', 'instance_id'),
    )

class MessageLog(Base):
    """Log of all processed messages"""
    __tablename__ = 'message_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), ForeignKey('groups.group_id'), nullable=False)
    message_id = Column(String(50), nullable=False)
    sender_id = Column(String(50))
    sender_name = Column(String(255))
    message_text = Column(Text)
    has_attachments = Column(Boolean, default=False)
    attachment_types = Column(ARRAY(Text))
    
    # Spam detection results
    is_spam = Column(Boolean)
    confidence_score = Column(DECIMAL(5,4))
    model_version = Column(String(50))
    processing_time_ms = Column(Integer)
    
    # Actions taken
    action_taken = Column(String(50))  # 'deleted', 'flagged', 'ignored', 'whitelisted'
    deletion_successful = Column(Boolean)
    notification_sent = Column(Boolean)
    
    # Timestamps
    message_created_at = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="message_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_logs_group_id', 'group_id'),
        Index('idx_message_logs_processed_at', 'processed_at'),
        Index('idx_message_logs_is_spam', 'is_spam'),
        Index('idx_message_logs_message_id', 'message_id'),
    )

class DailyStat(Base):
    """Daily aggregated statistics per group"""
    __tablename__ = 'daily_stats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), ForeignKey('groups.group_id'), nullable=False)
    date = Column(Date, nullable=False)
    
    # Message counts
    total_messages = Column(Integer, default=0)
    spam_detected = Column(Integer, default=0)
    spam_deleted = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    
    # Performance metrics
    avg_confidence_score = Column(DECIMAL(5,4))
    avg_processing_time_ms = Column(Integer)
    total_processing_time_ms = Column(Integer, default=0)
    
    # Error tracking
    api_errors = Column(Integer, default=0)
    deletion_failures = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="daily_stats")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'date'),
        Index('idx_daily_stats_group_date', 'group_id', 'date'),
        Index('idx_daily_stats_date', 'date'),
    )

class ModelVersion(Base):
    """ML model version tracking"""
    __tablename__ = 'model_versions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), unique=True, nullable=False)
    model_file_path = Column(String(500), nullable=False)
    vectorizer_file_path = Column(String(500), nullable=False)
    
    # Performance metrics
    accuracy = Column(DECIMAL(5,4))
    precision_score = Column(DECIMAL(5,4))
    recall_score = Column(DECIMAL(5,4))
    f1_score = Column(DECIMAL(5,4))
    
    # Training info
    training_data_size = Column(Integer)
    training_date = Column(DateTime(timezone=True))
    created_by = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_model_versions_version', 'version'),
        Index('idx_model_versions_active', 'is_active'),
    )

class SystemEvent(Base):
    """System audit log"""
    __tablename__ = 'system_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    
    # Event details
    description = Column(Text)
    details = Column(JSONB, default={})
    severity = Column(String(20), default='info')
    
    # Context
    user_id = Column(String(50))
    instance_name = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("severity IN ('debug', 'info', 'warning', 'error', 'critical')"),
        Index('idx_system_events_type', 'event_type'),
        Index('idx_system_events_created_at', 'created_at'),
        Index('idx_system_events_severity', 'severity'),
    )

class ConfigCache(Base):
    """Configuration cache for hot-reloading"""
    __tablename__ = 'config_cache'
    
    key = Column(String(255), primary_key=True)
    value = Column(JSONB, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PlatformUser(Base):
    """Platform users for admin dashboard"""
    __tablename__ = 'platform_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Permissions
    role = Column(String(20), default='viewer')
    permissions = Column(JSONB, default={})
    
    # Profile
    full_name = Column(String(255))
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'operator', 'viewer')"),
    )
