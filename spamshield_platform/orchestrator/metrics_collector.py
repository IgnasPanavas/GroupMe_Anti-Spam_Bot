"""
Metrics Collection System for SpamShield Platform
Collects, aggregates, and stores performance metrics
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading
import time
from collections import defaultdict, deque

from ..database.connection import get_database_manager
from ..database.models import MessageLog, DailyStat, Group, SystemEvent

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    group_id: str
    metric_name: str
    value: float
    tags: Dict[str, str] = None

class MetricsCollector:
    """
    Collects and aggregates metrics for the SpamShield platform
    """
    
    def __init__(self, aggregation_interval: int = 300):  # 5 minutes
        """
        Initialize metrics collector
        
        Args:
            aggregation_interval: How often to aggregate metrics (seconds)
        """
        self.db_manager = get_database_manager()
        self.aggregation_interval = aggregation_interval
        
        # In-memory metric buffers
        self.metric_buffer: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.realtime_metrics: Dict[str, Dict] = defaultdict(dict)
        
        # Background processing
        self.running = False
        self.aggregation_thread = None
        
        logger.info("MetricsCollector initialized")
    
    def start(self):
        """Start the metrics collection background tasks"""
        if self.running:
            return
        
        self.running = True
        self.aggregation_thread = threading.Thread(target=self._aggregation_loop, daemon=True)
        self.aggregation_thread.start()
        
        logger.info("MetricsCollector started")
    
    def stop(self):
        """Stop the metrics collection"""
        self.running = False
        if self.aggregation_thread:
            self.aggregation_thread.join(timeout=10)
        
        logger.info("MetricsCollector stopped")
    
    def record_metric(self, group_id: str, metric_name: str, value: float, tags: Dict[str, str] = None):
        """
        Record a single metric point
        
        Args:
            group_id: Group identifier
            metric_name: Name of the metric
            value: Metric value
            tags: Additional tags for the metric
        """
        metric_point = MetricPoint(
            timestamp=datetime.utcnow(),
            group_id=group_id,
            metric_name=metric_name,
            value=value,
            tags=tags or {}
        )
        
        self.metric_buffer.append(metric_point)
        
        # Update real-time metrics
        self.realtime_metrics[group_id][metric_name] = {
            'value': value,
            'timestamp': metric_point.timestamp,
            'tags': tags or {}
        }
    
    def record_message_processed(self, group_id: str, processing_time_ms: int, is_spam: bool, confidence: float):
        """Record metrics for a processed message"""
        self.record_metric(group_id, 'messages_processed', 1)
        self.record_metric(group_id, 'processing_time_ms', processing_time_ms)
        
        if is_spam:
            self.record_metric(group_id, 'spam_detected', 1)
            self.record_metric(group_id, 'spam_confidence', confidence)
    
    def record_spam_action(self, group_id: str, action: str, success: bool):
        """Record metrics for spam actions (deletion, notification, etc.)"""
        self.record_metric(group_id, f'spam_action_{action}', 1, {'success': str(success)})
    
    def record_api_call(self, group_id: str, api_endpoint: str, response_time_ms: int, success: bool):
        """Record metrics for API calls"""
        self.record_metric(group_id, 'api_calls', 1, {
            'endpoint': api_endpoint,
            'success': str(success)
        })
        self.record_metric(group_id, 'api_response_time_ms', response_time_ms, {
            'endpoint': api_endpoint
        })
    
    def record_error(self, group_id: str, error_type: str, error_message: str = None):
        """Record error metrics"""
        self.record_metric(group_id, 'errors', 1, {
            'error_type': error_type,
            'error_message': error_message[:100] if error_message else None
        })
    
    def get_realtime_metrics(self, group_id: Optional[str] = None) -> Dict:
        """
        Get current real-time metrics
        
        Args:
            group_id: Specific group ID, or None for all groups
            
        Returns:
            Dictionary of current metrics
        """
        if group_id:
            return self.realtime_metrics.get(group_id, {})
        
        return dict(self.realtime_metrics)
    
    def get_aggregated_metrics(self, group_id: str, start_date: date, end_date: date) -> Dict:
        """
        Get aggregated metrics for a date range
        
        Args:
            group_id: Group identifier
            start_date: Start date for metrics
            end_date: End date for metrics
            
        Returns:
            Dictionary of aggregated metrics
        """
        try:
            with self.db_manager.get_session() as session:
                stats = session.query(DailyStat).filter(
                    DailyStat.group_id == group_id,
                    DailyStat.date >= start_date,
                    DailyStat.date <= end_date
                ).order_by(DailyStat.date).all()
                
                return {
                    'dates': [stat.date.isoformat() for stat in stats],
                    'total_messages': [stat.total_messages for stat in stats],
                    'spam_detected': [stat.spam_detected for stat in stats],
                    'spam_deleted': [stat.spam_deleted for stat in stats],
                    'false_positives': [stat.false_positives for stat in stats],
                    'avg_confidence': [float(stat.avg_confidence_score) if stat.avg_confidence_score else 0 for stat in stats],
                    'avg_processing_time': [stat.avg_processing_time_ms for stat in stats],
                    'api_errors': [stat.api_errors for stat in stats],
                    'deletion_failures': [stat.deletion_failures for stat in stats]
                }
                
        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {e}")
            return {}
    
    def get_platform_summary(self) -> Dict:
        """Get platform-wide summary metrics"""
        try:
            with self.db_manager.get_session() as session:
                # Get today's stats
                today = date.today()
                today_stats = session.query(DailyStat).filter(
                    DailyStat.date == today
                ).all()
                
                # Get active groups count
                active_groups = session.query(Group).filter(
                    Group.status == 'active'
                ).count()
                
                # Calculate totals
                total_messages_today = sum(stat.total_messages for stat in today_stats)
                total_spam_detected_today = sum(stat.spam_detected for stat in today_stats)
                total_spam_deleted_today = sum(stat.spam_deleted for stat in today_stats)
                
                # Calculate averages
                avg_confidence = 0
                avg_processing_time = 0
                if today_stats:
                    confidence_scores = [float(stat.avg_confidence_score) for stat in today_stats if stat.avg_confidence_score]
                    if confidence_scores:
                        avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    
                    processing_times = [stat.avg_processing_time_ms for stat in today_stats if stat.avg_processing_time_ms]
                    if processing_times:
                        avg_processing_time = sum(processing_times) / len(processing_times)
                
                # Calculate spam rate
                spam_rate = (total_spam_detected_today / total_messages_today * 100) if total_messages_today > 0 else 0
                
                return {
                    'active_groups': active_groups,
                    'total_messages_today': total_messages_today,
                    'spam_detected_today': total_spam_detected_today,
                    'spam_deleted_today': total_spam_deleted_today,
                    'spam_rate_percent': round(spam_rate, 2),
                    'avg_confidence_score': round(avg_confidence, 3),
                    'avg_processing_time_ms': round(avg_processing_time, 1),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting platform summary: {e}")
            return {}
    
    def get_group_performance(self, group_id: str, days: int = 7) -> Dict:
        """
        Get performance metrics for a specific group
        
        Args:
            group_id: Group identifier
            days: Number of days to look back
            
        Returns:
            Performance metrics dictionary
        """
        try:
            with self.db_manager.get_session() as session:
                # Get recent stats
                start_date = date.today() - timedelta(days=days)
                stats = session.query(DailyStat).filter(
                    DailyStat.group_id == group_id,
                    DailyStat.date >= start_date
                ).order_by(DailyStat.date.desc()).all()
                
                if not stats:
                    return {'group_id': group_id, 'message': 'No data available'}
                
                # Calculate metrics
                total_messages = sum(stat.total_messages for stat in stats)
                total_spam = sum(stat.spam_detected for stat in stats)
                total_deleted = sum(stat.spam_deleted for stat in stats)
                total_false_positives = sum(stat.false_positives for stat in stats)
                
                # Calculate rates
                spam_rate = (total_spam / total_messages * 100) if total_messages > 0 else 0
                deletion_rate = (total_deleted / total_spam * 100) if total_spam > 0 else 0
                false_positive_rate = (total_false_positives / total_messages * 100) if total_messages > 0 else 0
                
                # Get latest stats
                latest_stat = stats[0]
                
                return {
                    'group_id': group_id,
                    'period_days': days,
                    'total_messages': total_messages,
                    'total_spam_detected': total_spam,
                    'total_spam_deleted': total_deleted,
                    'total_false_positives': total_false_positives,
                    'spam_rate_percent': round(spam_rate, 2),
                    'deletion_success_rate_percent': round(deletion_rate, 1),
                    'false_positive_rate_percent': round(false_positive_rate, 3),
                    'avg_confidence_score': float(latest_stat.avg_confidence_score) if latest_stat.avg_confidence_score else 0,
                    'avg_processing_time_ms': latest_stat.avg_processing_time_ms,
                    'last_updated': latest_stat.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting group performance: {e}")
            return {'group_id': group_id, 'error': str(e)}
    
    def _aggregation_loop(self):
        """Background thread for aggregating metrics"""
        while self.running:
            try:
                self._aggregate_daily_stats()
                time.sleep(self.aggregation_interval)
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")
                time.sleep(60)
    
    def _aggregate_daily_stats(self):
        """Aggregate daily statistics from message logs"""
        try:
            today = date.today()
            
            with self.db_manager.get_session() as session:
                # Get all groups
                groups = session.query(Group).filter(Group.status == 'active').all()
                
                for group in groups:
                    # Check if we already have stats for today
                    existing_stat = session.query(DailyStat).filter(
                        DailyStat.group_id == group.group_id,
                        DailyStat.date == today
                    ).first()
                    
                    # Get today's message logs
                    start_of_day = datetime.combine(today, datetime.min.time())
                    end_of_day = datetime.combine(today, datetime.max.time())
                    
                    logs = session.query(MessageLog).filter(
                        MessageLog.group_id == group.group_id,
                        MessageLog.processed_at >= start_of_day,
                        MessageLog.processed_at <= end_of_day
                    ).all()
                    
                    if not logs:
                        continue
                    
                    # Calculate aggregated metrics
                    total_messages = len(logs)
                    spam_logs = [log for log in logs if log.is_spam]
                    spam_detected = len(spam_logs)
                    spam_deleted = len([log for log in spam_logs if log.deletion_successful])
                    false_positives = len([log for log in logs if log.is_spam == False and 'false_positive' in (log.action_taken or '')])
                    
                    # Calculate averages
                    confidence_scores = [float(log.confidence_score) for log in spam_logs if log.confidence_score]
                    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                    
                    processing_times = [log.processing_time_ms for log in logs if log.processing_time_ms]
                    avg_processing_time = sum(processing_times) // len(processing_times) if processing_times else 0
                    total_processing_time = sum(processing_times)
                    
                    # Count errors
                    api_errors = len([log for log in logs if log.action_taken == 'error'])
                    deletion_failures = len([log for log in spam_logs if log.deletion_successful == False])
                    
                    # Create or update daily stat
                    if existing_stat:
                        existing_stat.total_messages = total_messages
                        existing_stat.spam_detected = spam_detected
                        existing_stat.spam_deleted = spam_deleted
                        existing_stat.false_positives = false_positives
                        existing_stat.avg_confidence_score = avg_confidence
                        existing_stat.avg_processing_time_ms = avg_processing_time
                        existing_stat.total_processing_time_ms = total_processing_time
                        existing_stat.api_errors = api_errors
                        existing_stat.deletion_failures = deletion_failures
                        existing_stat.updated_at = datetime.utcnow()
                    else:
                        daily_stat = DailyStat(
                            group_id=group.group_id,
                            date=today,
                            total_messages=total_messages,
                            spam_detected=spam_detected,
                            spam_deleted=spam_deleted,
                            false_positives=false_positives,
                            avg_confidence_score=avg_confidence,
                            avg_processing_time_ms=avg_processing_time,
                            total_processing_time_ms=total_processing_time,
                            api_errors=api_errors,
                            deletion_failures=deletion_failures
                        )
                        session.add(daily_stat)
                
                session.commit()
                logger.debug("Daily stats aggregation completed")
                
        except Exception as e:
            logger.error(f"Error aggregating daily stats: {e}")
    
    def cleanup_old_metrics(self, days_to_keep: int = 90):
        """
        Clean up old metric data
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            with self.db_manager.get_session() as session:
                # Clean up old daily stats
                deleted_stats = session.query(DailyStat).filter(
                    DailyStat.date < cutoff_date
                ).delete()
                
                # Clean up old message logs
                cutoff_datetime = datetime.combine(cutoff_date, datetime.min.time())
                deleted_logs = session.query(MessageLog).filter(
                    MessageLog.processed_at < cutoff_datetime
                ).delete()
                
                session.commit()
                
                logger.info(f"Cleaned up {deleted_stats} daily stats and {deleted_logs} message logs older than {days_to_keep} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector.start()
    return _metrics_collector
