"""
Metrics API for SpamShield Platform
Provides endpoints for retrieving analytics and performance metrics
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database.connection import get_db_session
from ...database.models import Group, MessageLog, DailyStat, SystemEvent
from ...orchestrator.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

# Pydantic models
class MetricsSummary(BaseModel):
    """Platform-wide metrics summary"""
    active_groups: int
    total_messages_today: int
    spam_detected_today: int
    spam_deleted_today: int
    spam_rate_percent: float
    avg_confidence_score: float
    avg_processing_time_ms: float
    last_updated: str

class GroupMetrics(BaseModel):
    """Metrics for a specific group"""
    group_id: str
    period_days: int
    total_messages: int
    total_spam_detected: int
    total_spam_deleted: int
    total_false_positives: int
    spam_rate_percent: float
    deletion_success_rate_percent: float
    false_positive_rate_percent: float
    avg_confidence_score: float
    avg_processing_time_ms: Optional[int]
    last_updated: str

class TimeSeriesData(BaseModel):
    """Time series data for charts"""
    dates: List[str]
    total_messages: List[int]
    spam_detected: List[int]
    spam_deleted: List[int]
    false_positives: List[int]
    avg_confidence: List[float]
    avg_processing_time: List[int]
    api_errors: List[int]
    deletion_failures: List[int]

class RealtimeMetrics(BaseModel):
    """Real-time metrics"""
    group_id: str
    metrics: dict
    timestamp: str

class SystemHealth(BaseModel):
    """System health metrics"""
    total_groups: int
    active_groups: int
    healthy_groups: int
    groups_with_errors: int
    total_instances: int
    healthy_instances: int
    avg_cpu_usage: float
    avg_memory_usage_mb: float
    last_updated: str

# Create API router
router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/summary", response_model=MetricsSummary)
async def get_metrics_summary():
    """
    Get platform-wide metrics summary
    """
    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_platform_summary()
        
        if not summary:
            raise HTTPException(status_code=503, detail="Metrics service unavailable")
        
        return MetricsSummary(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/groups/{group_id}", response_model=GroupMetrics)
async def get_group_metrics(
    group_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed metrics for a specific group
    """
    try:
        # Verify group exists
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get metrics
        metrics_collector = get_metrics_collector()
        metrics = metrics_collector.get_group_performance(group_id, days)
        
        if 'error' in metrics:
            raise HTTPException(status_code=500, detail=metrics['error'])
        
        return GroupMetrics(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group metrics for {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/groups/{group_id}/timeseries", response_model=TimeSeriesData)
async def get_group_timeseries(
    group_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session)
):
    """
    Get time series data for a group over a date range
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
        
        # Verify group exists
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get time series data
        metrics_collector = get_metrics_collector()
        timeseries = metrics_collector.get_aggregated_metrics(group_id, start_date, end_date)
        
        return TimeSeriesData(**timeseries)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeseries for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/groups/{group_id}/realtime", response_model=RealtimeMetrics)
async def get_realtime_metrics(
    group_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get real-time metrics for a group
    """
    try:
        # Verify group exists
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get real-time metrics
        metrics_collector = get_metrics_collector()
        realtime_data = metrics_collector.get_realtime_metrics(group_id)
        
        return RealtimeMetrics(
            group_id=group_id,
            metrics=realtime_data,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime metrics for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(db: Session = Depends(get_db_session)):
    """
    Get system health metrics
    """
    try:
        # Get group counts
        total_groups = db.query(Group).count()
        active_groups = db.query(Group).filter(Group.status == 'active').count()
        groups_with_errors = db.query(Group).filter(Group.error_count > 0).count()
        healthy_groups = active_groups - groups_with_errors
        
        # Get instance metrics (would need to implement BotInstance queries)
        from ...database.models import BotInstance
        total_instances = db.query(BotInstance).count()
        healthy_instances = db.query(BotInstance).filter(
            BotInstance.status == 'running'
        ).count()
        
        # Calculate average resource usage
        instances = db.query(BotInstance).filter(
            BotInstance.status == 'running'
        ).all()
        
        avg_cpu_usage = 0
        avg_memory_usage_mb = 0
        
        if instances:
            cpu_values = [float(inst.cpu_usage) for inst in instances if inst.cpu_usage]
            memory_values = [inst.memory_usage_mb for inst in instances if inst.memory_usage_mb]
            
            avg_cpu_usage = sum(cpu_values) / len(cpu_values) if cpu_values else 0
            avg_memory_usage_mb = sum(memory_values) / len(memory_values) if memory_values else 0
        
        return SystemHealth(
            total_groups=total_groups,
            active_groups=active_groups,
            healthy_groups=healthy_groups,
            groups_with_errors=groups_with_errors,
            total_instances=total_instances,
            healthy_instances=healthy_instances,
            avg_cpu_usage=round(avg_cpu_usage, 2),
            avg_memory_usage_mb=int(avg_memory_usage_mb),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/events")
async def get_system_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session)
):
    """
    Get system events with optional filtering
    """
    try:
        query = db.query(SystemEvent)
        
        # Apply filters
        if event_type:
            query = query.filter(SystemEvent.event_type == event_type)
        
        if severity:
            if severity not in ['debug', 'info', 'warning', 'error', 'critical']:
                raise HTTPException(status_code=400, detail="Invalid severity level")
            query = query.filter(SystemEvent.severity == severity)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        events = query.order_by(SystemEvent.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format events
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'entity_type': event.entity_type,
                'entity_id': event.entity_id,
                'description': event.description,
                'severity': event.severity,
                'details': event.details,
                'user_id': event.user_id,
                'instance_name': event.instance_name,
                'created_at': event.created_at.isoformat()
            })
        
        return {
            'events': formatted_events,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/top-spam-groups")
async def get_top_spam_groups(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db_session)
):
    """
    Get groups with the highest spam rates
    """
    try:
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Query for top spam groups
        spam_stats = db.query(
            DailyStat.group_id,
            func.sum(DailyStat.total_messages).label('total_messages'),
            func.sum(DailyStat.spam_detected).label('total_spam'),
            func.avg(DailyStat.avg_confidence_score).label('avg_confidence')
        ).filter(
            DailyStat.date >= start_date,
            DailyStat.date <= end_date
        ).group_by(DailyStat.group_id).having(
            func.sum(DailyStat.total_messages) > 0
        ).order_by(
            (func.sum(DailyStat.spam_detected) / func.sum(DailyStat.total_messages)).desc()
        ).limit(limit).all()
        
        # Get group names
        results = []
        for stat in spam_stats:
            group = db.query(Group).filter(Group.group_id == stat.group_id).first()
            spam_rate = (stat.total_spam / stat.total_messages * 100) if stat.total_messages > 0 else 0
            
            results.append({
                'group_id': stat.group_id,
                'group_name': group.group_name if group else 'Unknown',
                'total_messages': stat.total_messages,
                'total_spam': stat.total_spam,
                'spam_rate_percent': round(spam_rate, 2),
                'avg_confidence': round(float(stat.avg_confidence), 3) if stat.avg_confidence else 0
            })
        
        return {
            'period_days': days,
            'top_groups': results,
            'total_groups': len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting top spam groups: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/performance-trends")
async def get_performance_trends(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db_session)
):
    """
    Get platform performance trends over time
    """
    try:
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Query daily aggregated stats
        daily_trends = db.query(
            DailyStat.date,
            func.sum(DailyStat.total_messages).label('total_messages'),
            func.sum(DailyStat.spam_detected).label('spam_detected'),
            func.sum(DailyStat.spam_deleted).label('spam_deleted'),
            func.avg(DailyStat.avg_confidence_score).label('avg_confidence'),
            func.avg(DailyStat.avg_processing_time_ms).label('avg_processing_time'),
            func.sum(DailyStat.api_errors).label('api_errors')
        ).filter(
            DailyStat.date >= start_date,
            DailyStat.date <= end_date
        ).group_by(DailyStat.date).order_by(DailyStat.date).all()
        
        # Format results
        trends = {
            'dates': [],
            'total_messages': [],
            'spam_detected': [],
            'spam_deleted': [],
            'spam_rate_percent': [],
            'avg_confidence': [],
            'avg_processing_time_ms': [],
            'api_errors': []
        }
        
        for trend in daily_trends:
            trends['dates'].append(trend.date.isoformat())
            trends['total_messages'].append(trend.total_messages or 0)
            trends['spam_detected'].append(trend.spam_detected or 0)
            trends['spam_deleted'].append(trend.spam_deleted or 0)
            
            # Calculate spam rate
            spam_rate = (trend.spam_detected / trend.total_messages * 100) if trend.total_messages > 0 else 0
            trends['spam_rate_percent'].append(round(spam_rate, 2))
            
            trends['avg_confidence'].append(round(float(trend.avg_confidence), 3) if trend.avg_confidence else 0)
            trends['avg_processing_time_ms'].append(int(trend.avg_processing_time) if trend.avg_processing_time else 0)
            trends['api_errors'].append(trend.api_errors or 0)
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trends': trends
        }
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_metrics_router():
    """Get the metrics API router"""
    return router
