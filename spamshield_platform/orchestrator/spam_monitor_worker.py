"""
SpamMonitor Worker - Platform-integrated version of the original SpamMonitor
"""

import asyncio
import logging
import multiprocessing
import os
import pickle
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import threading

# Add the project root to the path to import the original modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from ..database.connection import get_database_manager
from ..database.models import Group, GroupConfig, MessageLog, DailyStat, SystemEvent
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

class SpamMonitorWorker:
    """
    Platform-integrated SpamMonitor worker that can handle multiple groups
    and integrates with the database for configuration and metrics
    """
    
    def __init__(self, worker_id: str, assigned_groups: Set[str], orchestrator_name: str):
        """
        Initialize the SpamMonitor worker
        
        Args:
            worker_id: Unique identifier for this worker
            assigned_groups: Set of group IDs to monitor
            orchestrator_name: Name of the parent orchestrator
        """
        self.worker_id = worker_id
        self.assigned_groups = assigned_groups
        self.orchestrator_name = orchestrator_name
        self.db_manager = get_database_manager()
        self.metrics_collector = MetricsCollector()
        
        # Group monitoring state
        self.group_monitors: Dict[str, GroupMonitor] = {}
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Load ML model once for all groups
        self.model = None
        self.vectorizer = None
        self.model_version = None
        self._load_model()
        
        logger.info(f"SpamMonitor Worker {worker_id} initialized with {len(assigned_groups)} groups")
    
    def _load_model(self):
        """Load the spam detection model"""
        try:
            # Load the trained model
            model_file = 'data/training/spam_detection_model.pkl'
            vectorizer_file = 'data/training/tfidf_vectorizer.pkl'
            
            if os.path.exists(model_file) and os.path.exists(vectorizer_file):
                with open(model_file, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                
                self.model_version = "1.0.0"
                logger.info(f"Loaded model version {self.model_version}")
            else:
                logger.error("Model files not found")
                raise FileNotFoundError("Model files not found")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    async def start(self):
        """Start the worker and initialize group monitors"""
        logger.info(f"Starting SpamMonitor Worker {self.worker_id}")
        
        self.running = True
        
        # Initialize monitors for each assigned group
        for group_id in self.assigned_groups:
            await self._initialize_group_monitor(group_id)
        
        # Start monitoring loop
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Wait for shutdown
        try:
            await asyncio.gather(monitoring_task, heartbeat_task)
        except asyncio.CancelledError:
            logger.info("Worker tasks cancelled")
    
    async def stop(self):
        """Stop the worker and cleanup"""
        logger.info(f"Stopping SpamMonitor Worker {self.worker_id}")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop all group monitors
        for group_id, monitor in self.group_monitors.items():
            await monitor.stop()
        
        logger.info(f"SpamMonitor Worker {self.worker_id} stopped")
    
    async def _initialize_group_monitor(self, group_id: str):
        """Initialize monitoring for a specific group"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(Group).filter(Group.group_id == group_id).first()
                config = session.query(GroupConfig).filter(GroupConfig.group_id == group_id).first()
                
                if not group:
                    logger.error(f"Group {group_id} not found in database")
                    return
                
                if not config:
                    logger.warning(f"No config found for group {group_id}, using defaults")
                    config = GroupConfig(group_id=group_id)
                
                # Create group monitor
                monitor = GroupMonitor(
                    group=group,
                    config=config,
                    model=self.model,
                    vectorizer=self.vectorizer,
                    model_version=self.model_version,
                    db_manager=self.db_manager,
                    metrics_collector=self.metrics_collector
                )
                
                self.group_monitors[group_id] = monitor
                await monitor.initialize()
                
                logger.info(f"Initialized monitor for group {group_id} ({group.group_name})")
                
        except Exception as e:
            logger.error(f"Failed to initialize group monitor for {group_id}: {e}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for all assigned groups"""
        while self.running:
            try:
                # Process messages for each group
                tasks = []
                for group_id, monitor in self.group_monitors.items():
                    if monitor.is_active():
                        task = asyncio.create_task(monitor.process_messages())
                        tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait for next cycle (minimum interval across all groups)
                min_interval = min(
                    (monitor.config_values['check_interval_seconds'] for monitor in self.group_monitors.values()),
                    default=30
                )
                await asyncio.sleep(min_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to show worker is alive"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)
    
    async def _send_heartbeat(self):
        """Send heartbeat with worker status"""
        try:
            # Update worker status in database or send to orchestrator
            # For now, just log the heartbeat
            active_groups = sum(1 for monitor in self.group_monitors.values() if monitor.is_active())
            logger.debug(f"Worker {self.worker_id} heartbeat: {active_groups} active groups")
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    @staticmethod
    def run_worker(worker_id: str, assigned_groups: Set[str], orchestrator_name: str):
        """Static method to run worker in a separate process"""
        # Set up logging for the worker process
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - Worker-{worker_id} - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handle shutdown signals
        def signal_handler(signum, frame):
            logger.info(f"Worker {worker_id} received signal {signum}")
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create and run worker
        worker = SpamMonitorWorker(worker_id, assigned_groups, orchestrator_name)
        
        try:
            asyncio.run(worker.start())
        except KeyboardInterrupt:
            logger.info(f"Worker {worker_id} interrupted by user")
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
        finally:
            logger.info(f"Worker {worker_id} exiting")


class GroupMonitor:
    """Monitor for a single GroupMe group"""
    
    def __init__(self, group, config, model, vectorizer, model_version, db_manager, metrics_collector):
        """
        Initialize group monitor
        
        Args:
            group: Group database model
            config: GroupConfig database model
            model: ML model for spam detection
            vectorizer: TF-IDF vectorizer
            model_version: Version of the ML model
            db_manager: Database manager instance
            metrics_collector: Metrics collector instance
        """
        self.group = group
        self.group_id = group.group_id
        # Store config values instead of the SQLAlchemy object
        self.config_values = {
            'send_startup_message': config.send_startup_message,
            'confidence_threshold': config.confidence_threshold,
            'auto_delete_spam': config.auto_delete_spam,
            'notify_on_removal': config.notify_on_removal,
            'notify_admins': config.notify_admins,
            'whitelist_users': config.whitelist_users or [],
            'check_interval_seconds': config.check_interval_seconds
        }
        self.model = model
        self.vectorizer = vectorizer
        self.model_version = model_version
        self.db_manager = db_manager
        self.metrics_collector = metrics_collector
        
        # GroupMe API client (would need to implement this)
        self.api_client = None  # TODO: Initialize GroupMe API client
        
        # Monitoring state
        self.last_message_id = group.last_message_id
        self.processed_messages = set()
        self.active = True
        
        # Statistics
        self.messages_processed = 0
        self.spam_detected = 0
        self.spam_deleted = 0
        self.errors = 0
        
        logger.info(f"GroupMonitor initialized for {group.group_id} ({group.group_name})")
    
    async def initialize(self):
        """Initialize the group monitor"""
        try:
            # Send startup message if configured
            if self.config_values['send_startup_message']:
                await self._send_startup_message()
            
            # Load recent message IDs to avoid reprocessing
            await self._load_processed_messages()
            
            logger.info(f"Group monitor for {self.group.group_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize group monitor for {self.group.group_id}: {e}")
            self.active = False
    
    async def process_messages(self):
        """Process recent messages for spam detection"""
        if not self.active:
            return
        
        try:
            start_time = time.time()
            
            # Get recent messages (would implement GroupMe API call)
            messages = await self._get_recent_messages()
            
            if not messages:
                return
            
            new_messages = 0
            for message in messages:
                if await self._process_single_message(message):
                    new_messages += 1
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if new_messages > 0:
                logger.info(f"Group {self.group.group_id}: Processed {new_messages} new messages in {processing_time}ms")
            
            # Update group last checked time
            await self._update_group_status()
            
        except Exception as e:
            logger.error(f"Error processing messages for group {self.group.group_id}: {e}")
            self.errors += 1
    
    async def _process_single_message(self, message: dict) -> bool:
        """
        Process a single message for spam detection
        
        Args:
            message: Message dictionary from GroupMe API
            
        Returns:
            bool: True if message was processed (new), False if already processed
        """
        message_id = message.get('id')
        
        # Skip if already processed
        if message_id in self.processed_messages:
            return False
        
        # Skip if this is an old message
        if message_id == self.last_message_id:
            return False
        
        start_time = time.time()
        
        try:
            sender_name = message.get('name', 'Unknown')
            sender_id = message.get('user_id', '')
            text = message.get('text', '')
            attachments = message.get('attachments', [])
            message_created_at = datetime.fromtimestamp(message.get('created_at', time.time()))
            
            # Check if user is whitelisted
            if sender_id in self.config_values['whitelist_users']:
                logger.debug(f"Skipping whitelisted user {sender_name}")
                self.processed_messages.add(message_id)
                return True
            
            # Detect spam
            is_spam, confidence = await self._detect_spam(message)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log message processing
            await self._log_message(
                message_id=message_id,
                sender_id=sender_id,
                sender_name=sender_name,
                message_text=text,
                has_attachments=len(attachments) > 0,
                attachment_types=[att.get('type') for att in attachments],
                is_spam=is_spam,
                confidence_score=confidence,
                processing_time_ms=processing_time_ms,
                message_created_at=message_created_at
            )
            
            # Take action if spam detected
            if is_spam:
                await self._handle_spam_message(message, confidence)
                self.spam_detected += 1
            
            self.messages_processed += 1
            self.processed_messages.add(message_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")
            self.errors += 1
            return False
    
    async def _detect_spam(self, message: dict) -> tuple[bool, float]:
        """
        Detect if a message is spam using the ML model
        
        Args:
            message: Message dictionary
            
        Returns:
            tuple: (is_spam, confidence_score)
        """
        try:
            text = message.get('text', '')
            attachments = message.get('attachments', [])
            
            # Skip detection for messages with only attachments and no text
            if not text and attachments:
                return False, 0.0
            
            if not text:
                return False, 0.0
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            if not processed_text:
                return False, 0.0
            
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
            
            is_spam = prediction == 'spam' and confidence >= float(self.config_values['confidence_threshold'])
            
            return is_spam, float(confidence)
            
        except Exception as e:
            logger.error(f"Error detecting spam: {e}")
            return False, 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for ML model"""
        import re
        
        if not text:
            return ''
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _handle_spam_message(self, message: dict, confidence: float):
        """Handle a detected spam message"""
        message_id = message.get('id')
        sender_name = message.get('name', 'Unknown')
        
        try:
            action_taken = "flagged"
            deletion_successful = False
            notification_sent = False
            
            # Try to delete the message if configured
            if self.config_values['auto_delete_spam']:
                if await self._delete_message(message_id):
                    action_taken = "deleted"
                    deletion_successful = True
                    self.spam_deleted += 1
                    
                    # Send removal notification if configured
                    if self.config_values['notify_on_removal']:
                        notification_sent = await self._send_removal_notification(sender_name)
                else:
                    # If deletion failed, send spam alert
                    if self.config_values['notify_admins']:
                        notification_sent = await self._send_spam_alert(message, confidence)
            else:
                # Just send alert without deleting
                if self.config_values['notify_admins']:
                    notification_sent = await self._send_spam_alert(message, confidence)
            
            # Update message log with action results
            await self._update_message_log(
                message_id=message_id,
                action_taken=action_taken,
                deletion_successful=deletion_successful,
                notification_sent=notification_sent
            )
            
            logger.info(f"Handled spam from {sender_name}: {action_taken} (confidence: {confidence:.3f})")
            
        except Exception as e:
            logger.error(f"Error handling spam message {message_id}: {e}")
    
    async def _get_recent_messages(self) -> List[dict]:
        """Get recent messages from GroupMe API"""
        # TODO: Implement GroupMe API call
        # This would use the original GroupMe API client
        return []
    
    async def _delete_message(self, message_id: str) -> bool:
        """Delete a message via GroupMe API"""
        # TODO: Implement GroupMe API call
        return False
    
    async def _send_startup_message(self):
        """Send startup notification to the group"""
        # TODO: Implement GroupMe API call
        pass
    
    async def _send_removal_notification(self, sender_name: str) -> bool:
        """Send notification that spam was removed"""
        # TODO: Implement GroupMe API call
        return False
    
    async def _send_spam_alert(self, message: dict, confidence: float) -> bool:
        """Send spam alert notification"""
        # TODO: Implement GroupMe API call
        return False
    
    async def _log_message(self, **kwargs):
        """Log message processing to database"""
        try:
            with self.db_manager.get_session() as session:
                log_entry = MessageLog(
                    group_id=self.group.group_id,
                    model_version=self.model_version,
                    **kwargs
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
    
    async def _update_message_log(self, message_id: str, **kwargs):
        """Update message log with action results"""
        try:
            with self.db_manager.get_session() as session:
                log_entry = session.query(MessageLog).filter(
                    MessageLog.message_id == message_id,
                    MessageLog.group_id == self.group.group_id
                ).first()
                
                if log_entry:
                    for key, value in kwargs.items():
                        setattr(log_entry, key, value)
                    session.commit()
        except Exception as e:
            logger.error(f"Failed to update message log: {e}")
    
    async def _load_processed_messages(self):
        """Load recently processed message IDs to avoid reprocessing"""
        try:
            with self.db_manager.get_session() as session:
                # Get message IDs from the last hour
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                recent_logs = session.query(MessageLog.message_id).filter(
                    MessageLog.group_id == self.group.group_id,
                    MessageLog.processed_at >= cutoff_time
                ).all()
                
                self.processed_messages = {log.message_id for log in recent_logs}
                
        except Exception as e:
            logger.error(f"Failed to load processed messages: {e}")
    
    async def _update_group_status(self):
        """Update group last checked timestamp"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(Group).filter(Group.group_id == self.group.group_id).first()
                if group:
                    group.last_checked = datetime.utcnow()
                    if self.last_message_id:
                        group.last_message_id = self.last_message_id
                    session.commit()
        except Exception as e:
            logger.error(f"Failed to update group status: {e}")
    
    async def stop(self):
        """Stop monitoring this group"""
        self.active = False
        logger.info(f"Stopped monitoring group {self.group.group_id}")
    
    def is_active(self) -> bool:
        """Check if this group monitor is active"""
        return self.active
