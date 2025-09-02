"""
Group Management API for SpamShield Platform
Provides endpoints for adding, removing, and managing monitored groups
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database.connection import get_db_session
from ...database.models import Group, GroupConfig, GroupAssignment, BotInstance, SystemEvent
from ...orchestrator.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

# Pydantic models
class GroupCreate(BaseModel):
    """Model for creating a new group"""
    group_id: str = Field(..., min_length=1, max_length=50)
    group_name: str = Field(..., min_length=1, max_length=255)
    owner_id: Optional[str] = Field(None, max_length=50)
    owner_name: Optional[str] = Field(None, max_length=255)

class GroupUpdate(BaseModel):
    """Model for updating group information"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=255)
    owner_id: Optional[str] = Field(None, max_length=50)
    owner_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|inactive|paused|error)$")

class GroupResponse(BaseModel):
    """Model for group response"""
    id: str
    group_id: str
    group_name: str
    status: str
    owner_id: Optional[str]
    owner_name: Optional[str]
    member_count: int
    created_at: datetime
    updated_at: datetime
    last_checked: Optional[datetime]
    last_message_id: Optional[str]
    error_count: int
    error_message: Optional[str]
    
    # Assignment info
    assigned_instance: Optional[str] = None
    instance_status: Optional[str] = None

class GroupListResponse(BaseModel):
    """Model for group list response"""
    groups: List[GroupResponse]
    total_count: int
    active_count: int
    inactive_count: int

# Create API router
router = APIRouter(prefix="/groups", tags=["group_management"])

@router.get("/", response_model=GroupListResponse)
async def list_groups(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session)
):
    """
    List all monitored groups with optional filtering
    """
    try:
        query = db.query(Group)
        
        # Filter by status if provided
        if status:
            if status not in ['active', 'inactive', 'paused', 'error']:
                raise HTTPException(status_code=400, detail="Invalid status filter")
            query = query.filter(Group.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        groups = query.order_by(Group.updated_at.desc()).offset(offset).limit(limit).all()
        
        # Get assignment information
        group_responses = []
        for group in groups:
            # Get assignment info
            assignment = db.query(GroupAssignment).filter(
                GroupAssignment.group_id == group.group_id
            ).first()
            
            assigned_instance = None
            instance_status = None
            
            if assignment:
                instance = db.query(BotInstance).filter(
                    BotInstance.id == assignment.instance_id
                ).first()
                if instance:
                    assigned_instance = instance.instance_name
                    instance_status = instance.status
            
            group_responses.append(GroupResponse(
                id=str(group.id),
                group_id=group.group_id,
                group_name=group.group_name,
                status=group.status,
                owner_id=group.owner_id,
                owner_name=group.owner_name,
                member_count=group.member_count,
                created_at=group.created_at,
                updated_at=group.updated_at,
                last_checked=group.last_checked,
                last_message_id=group.last_message_id,
                error_count=group.error_count,
                error_message=group.error_message,
                assigned_instance=assigned_instance,
                instance_status=instance_status
            ))
        
        # Get status counts
        status_counts = db.query(Group.status, func.count(Group.id)).group_by(Group.status).all()
        status_dict = {status: count for status, count in status_counts}
        
        return GroupListResponse(
            groups=group_responses,
            total_count=total_count,
            active_count=status_dict.get('active', 0),
            inactive_count=status_dict.get('inactive', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get detailed information about a specific group
    """
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get assignment info
        assignment = db.query(GroupAssignment).filter(
            GroupAssignment.group_id == group_id
        ).first()
        
        assigned_instance = None
        instance_status = None
        
        if assignment:
            instance = db.query(BotInstance).filter(
                BotInstance.id == assignment.instance_id
            ).first()
            if instance:
                assigned_instance = instance.instance_name
                instance_status = instance.status
        
        return GroupResponse(
            id=str(group.id),
            group_id=group.group_id,
            group_name=group.group_name,
            status=group.status,
            owner_id=group.owner_id,
            owner_name=group.owner_name,
            member_count=group.member_count,
            created_at=group.created_at,
            updated_at=group.updated_at,
            last_checked=group.last_checked,
            last_message_id=group.last_message_id,
            error_count=group.error_count,
            error_message=group.error_message,
            assigned_instance=assigned_instance,
            instance_status=instance_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=GroupResponse)
async def add_group(
    group_data: GroupCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Add a new group to monitoring
    """
    try:
        # Check if group already exists
        existing_group = db.query(Group).filter(Group.group_id == group_data.group_id).first()
        if existing_group:
            raise HTTPException(status_code=409, detail=f"Group {group_data.group_id} already exists")
        
        # Create group record
        group = Group(
            group_id=group_data.group_id,
            group_name=group_data.group_name,
            owner_id=group_data.owner_id,
            owner_name=group_data.owner_name,
            status='active'
        )
        db.add(group)
        
        # Create default configuration
        config = GroupConfig(group_id=group_data.group_id)
        db.add(config)
        
        db.commit()
        db.refresh(group)
        
        # Log system event
        event = SystemEvent(
            event_type='group_added',
            entity_type='group',
            entity_id=group_data.group_id,
            description=f"Group '{group_data.group_name}' added to monitoring",
            severity='info'
        )
        db.add(event)
        db.commit()
        
        # Trigger orchestrator to assign the group
        background_tasks.add_task(_notify_orchestrator_group_change)
        
        logger.info(f"Added group {group_data.group_id} ({group_data.group_name}) to monitoring")
        
        return await get_group(group_data.group_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding group {group_data.group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    group_update: GroupUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update group information
    """
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Track changes
        changes = {}
        
        # Update fields
        for field, value in group_update.dict(exclude_unset=True).items():
            old_value = getattr(group, field)
            if old_value != value:
                changes[field] = {'old': old_value, 'new': value}
                setattr(group, field, value)
        
        if not changes:
            return await get_group(group_id, db)
        
        group.updated_at = datetime.utcnow()
        db.commit()
        
        # Log changes
        change_summary = ", ".join([f"{k}: {v['old']} -> {v['new']}" for k, v in changes.items()])
        event = SystemEvent(
            event_type='group_updated',
            entity_type='group',
            entity_id=group_id,
            description=f"Group updated: {change_summary}",
            severity='info',
            details={'changes': changes}
        )
        db.add(event)
        db.commit()
        
        logger.info(f"Updated group {group_id}: {list(changes.keys())}")
        
        return await get_group(group_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{group_id}")
async def remove_group(
    group_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Remove a group from monitoring
    """
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Mark as inactive instead of deleting (preserve data)
        group.status = 'inactive'
        group.updated_at = datetime.utcnow()
        db.commit()
        
        # Log removal
        event = SystemEvent(
            event_type='group_removed',
            entity_type='group',
            entity_id=group_id,
            description=f"Group '{group.group_name}' removed from monitoring",
            severity='info'
        )
        db.add(event)
        db.commit()
        
        # Notify orchestrator
        background_tasks.add_task(_notify_orchestrator_group_change)
        
        logger.info(f"Removed group {group_id} from monitoring")
        
        return {"message": f"Group {group_id} removed from monitoring", "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{group_id}/activate")
async def activate_group(
    group_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Activate monitoring for a group
    """
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        if group.status == 'active':
            return {"message": f"Group {group_id} is already active", "status": "no_change"}
        
        group.status = 'active'
        group.updated_at = datetime.utcnow()
        group.error_count = 0  # Reset error count
        group.error_message = None
        db.commit()
        
        # Log activation
        event = SystemEvent(
            event_type='group_activated',
            entity_type='group',
            entity_id=group_id,
            description=f"Group '{group.group_name}' activated for monitoring",
            severity='info'
        )
        db.add(event)
        db.commit()
        
        # Notify orchestrator
        background_tasks.add_task(_notify_orchestrator_group_change)
        
        logger.info(f"Activated group {group_id}")
        
        return {"message": f"Group {group_id} activated", "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{group_id}/deactivate")
async def deactivate_group(
    group_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Deactivate monitoring for a group
    """
    try:
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        if group.status == 'inactive':
            return {"message": f"Group {group_id} is already inactive", "status": "no_change"}
        
        group.status = 'inactive'
        group.updated_at = datetime.utcnow()
        db.commit()
        
        # Log deactivation
        event = SystemEvent(
            event_type='group_deactivated',
            entity_type='group',
            entity_id=group_id,
            description=f"Group '{group.group_name}' deactivated",
            severity='info'
        )
        db.add(event)
        db.commit()
        
        # Notify orchestrator
        background_tasks.add_task(_notify_orchestrator_group_change)
        
        logger.info(f"Deactivated group {group_id}")
        
        return {"message": f"Group {group_id} deactivated", "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{group_id}/performance")
async def get_group_performance(
    group_id: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db_session)
):
    """
    Get performance metrics for a group
    """
    try:
        # Verify group exists
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get performance metrics
        metrics_collector = get_metrics_collector()
        performance = metrics_collector.get_group_performance(group_id, days)
        
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _notify_orchestrator_group_change():
    """Notify orchestrator about group changes"""
    try:
        # This would trigger the orchestrator to reassign groups
        # For now, we'll just log it
        logger.info("Group change notification sent to orchestrator")
    except Exception as e:
        logger.error(f"Error notifying orchestrator: {e}")

def get_group_router():
    """Get the group management API router"""
    return router
