"""
Configuration API for SpamShield Platform
Provides RESTful endpoints for managing group configurations with hot-reload capability
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ...database.connection import get_db_session
from ...database.models import Group, GroupConfig, SystemEvent, ConfigCache
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class GroupConfigUpdate(BaseModel):
    """Model for updating group configuration"""
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    check_interval_seconds: Optional[int] = Field(None, ge=5, le=3600)
    auto_delete_spam: Optional[bool] = None
    notify_on_removal: Optional[bool] = None
    notify_admins: Optional[bool] = None
    send_startup_message: Optional[bool] = None
    max_message_age_hours: Optional[int] = Field(None, ge=1, le=168)  # 1 hour to 1 week
    batch_size: Optional[int] = Field(None, ge=1, le=100)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    model_version: Optional[str] = None
    custom_keywords: Optional[List[str]] = None
    whitelist_users: Optional[List[str]] = None

class GroupConfigResponse(BaseModel):
    """Model for group configuration response"""
    group_id: str
    group_name: str
    confidence_threshold: float
    check_interval_seconds: int
    auto_delete_spam: bool
    notify_on_removal: bool
    notify_admins: bool
    send_startup_message: bool
    max_message_age_hours: int
    batch_size: int
    rate_limit_per_minute: int
    model_version: str
    custom_keywords: List[str]
    whitelist_users: List[str]
    created_at: datetime
    updated_at: datetime

class BulkConfigUpdate(BaseModel):
    """Model for bulk configuration updates"""
    group_ids: List[str] = Field(..., min_items=1)
    config_updates: GroupConfigUpdate

class ConfigTemplate(BaseModel):
    """Model for configuration templates"""
    name: str
    description: str
    config: GroupConfigUpdate

# Create API router
router = APIRouter(prefix="/config", tags=["configuration"])

# Initialize config manager
config_manager = ConfigManager()

@router.get("/groups/{group_id}", response_model=GroupConfigResponse)
async def get_group_config(
    group_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get configuration for a specific group
    """
    try:
        # Get group and config from database
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        config = db.query(GroupConfig).filter(GroupConfig.group_id == group_id).first()
        if not config:
            # Create default config if none exists
            config = GroupConfig(group_id=group_id)
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return GroupConfigResponse(
            group_id=group.group_id,
            group_name=group.group_name,
            confidence_threshold=float(config.confidence_threshold),
            check_interval_seconds=config.check_interval_seconds,
            auto_delete_spam=config.auto_delete_spam,
            notify_on_removal=config.notify_on_removal,
            notify_admins=config.notify_admins,
            send_startup_message=config.send_startup_message,
            max_message_age_hours=config.max_message_age_hours,
            batch_size=config.batch_size,
            rate_limit_per_minute=config.rate_limit_per_minute,
            model_version=config.model_version,
            custom_keywords=config.custom_keywords or [],
            whitelist_users=config.whitelist_users or [],
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group config for {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/groups/{group_id}", response_model=GroupConfigResponse)
async def update_group_config(
    group_id: str,
    config_update: GroupConfigUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Update configuration for a specific group
    """
    try:
        # Get group and config
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        config = db.query(GroupConfig).filter(GroupConfig.group_id == group_id).first()
        if not config:
            config = GroupConfig(group_id=group_id)
            db.add(config)
        
        # Track changes for logging
        changes = {}
        
        # Update configuration fields
        for field, value in config_update.dict(exclude_unset=True).items():
            old_value = getattr(config, field)
            if old_value != value:
                changes[field] = {'old': old_value, 'new': value}
                setattr(config, field, value)
        
        if not changes:
            # No changes made
            return await get_group_config(group_id, db)
        
        # Save changes
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        
        # Log configuration change
        await _log_config_change(group_id, changes, db)
        
        # Trigger hot-reload in background
        background_tasks.add_task(config_manager.notify_config_change, group_id)
        
        logger.info(f"Updated configuration for group {group_id}: {list(changes.keys())}")
        
        return await get_group_config(group_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group config for {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/groups/bulk-update")
async def bulk_update_configs(
    bulk_update: BulkConfigUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Update configuration for multiple groups at once
    """
    try:
        results = []
        errors = []
        
        for group_id in bulk_update.group_ids:
            try:
                # Verify group exists
                group = db.query(Group).filter(Group.group_id == group_id).first()
                if not group:
                    errors.append(f"Group {group_id} not found")
                    continue
                
                # Update config
                config = db.query(GroupConfig).filter(GroupConfig.group_id == group_id).first()
                if not config:
                    config = GroupConfig(group_id=group_id)
                    db.add(config)
                
                # Apply updates
                changes = {}
                for field, value in bulk_update.config_updates.dict(exclude_unset=True).items():
                    old_value = getattr(config, field)
                    if old_value != value:
                        changes[field] = {'old': old_value, 'new': value}
                        setattr(config, field, value)
                
                if changes:
                    config.updated_at = datetime.utcnow()
                    await _log_config_change(group_id, changes, db)
                    background_tasks.add_task(config_manager.notify_config_change, group_id)
                    results.append({'group_id': group_id, 'status': 'updated', 'changes': list(changes.keys())})
                else:
                    results.append({'group_id': group_id, 'status': 'no_changes'})
                
            except Exception as e:
                errors.append(f"Error updating {group_id}: {str(e)}")
        
        db.commit()
        
        return {
            'results': results,
            'errors': errors,
            'total_groups': len(bulk_update.group_ids),
            'updated': len([r for r in results if r['status'] == 'updated']),
            'no_changes': len([r for r in results if r['status'] == 'no_changes']),
            'errors': len(errors)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk config update: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/groups/{group_id}/history")
async def get_config_history(
    group_id: str,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """
    Get configuration change history for a group
    """
    try:
        # Get configuration change events
        events = db.query(SystemEvent).filter(
            SystemEvent.event_type == 'config_changed',
            SystemEvent.entity_id == group_id
        ).order_by(SystemEvent.created_at.desc()).limit(limit).all()
        
        history = []
        for event in events:
            history.append({
                'timestamp': event.created_at.isoformat(),
                'description': event.description,
                'changes': event.details.get('changes', {}),
                'user_id': event.user_id,
                'instance_name': event.instance_name
            })
        
        return {
            'group_id': group_id,
            'history': history,
            'total_entries': len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting config history for {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/groups/{group_id}/reset")
async def reset_group_config(
    group_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Reset group configuration to defaults
    """
    try:
        # Get group
        group = db.query(Group).filter(Group.group_id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
        
        # Get current config
        config = db.query(GroupConfig).filter(GroupConfig.group_id == group_id).first()
        if not config:
            raise HTTPException(status_code=404, detail=f"Config for group {group_id} not found")
        
        # Create new default config
        old_config_dict = config.to_dict()
        
        # Reset to defaults
        default_config = GroupConfig(group_id=group_id)
        for key, value in default_config.to_dict().items():
            if key not in ['group_id']:
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        db.commit()
        
        # Log the reset
        await _log_system_event(
            db,
            'config_reset',
            'group',
            group_id,
            f"Configuration reset to defaults for group {group.group_name}",
            details={'old_config': old_config_dict, 'new_config': config.to_dict()}
        )
        
        # Trigger hot-reload
        background_tasks.add_task(config_manager.notify_config_change, group_id)
        
        logger.info(f"Reset configuration for group {group_id} to defaults")
        
        return await get_group_config(group_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting config for {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/templates")
async def get_config_templates():
    """
    Get available configuration templates
    """
    templates = [
        ConfigTemplate(
            name="strict",
            description="Strict spam detection with low tolerance",
            config=GroupConfigUpdate(
                confidence_threshold=0.7,
                check_interval_seconds=15,
                auto_delete_spam=True,
                notify_on_removal=True,
                notify_admins=True
            )
        ),
        ConfigTemplate(
            name="balanced",
            description="Balanced spam detection for most groups",
            config=GroupConfigUpdate(
                confidence_threshold=0.8,
                check_interval_seconds=30,
                auto_delete_spam=True,
                notify_on_removal=False,
                notify_admins=True
            )
        ),
        ConfigTemplate(
            name="conservative",
            description="Conservative detection with high confidence threshold",
            config=GroupConfigUpdate(
                confidence_threshold=0.9,
                check_interval_seconds=60,
                auto_delete_spam=False,
                notify_on_removal=False,
                notify_admins=True
            )
        )
    ]
    
    return {'templates': templates}

@router.post("/groups/{group_id}/apply-template")
async def apply_config_template(
    group_id: str,
    template_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Apply a configuration template to a group
    """
    try:
        # Get available templates
        templates_response = await get_config_templates()
        templates = {t.name: t for t in templates_response['templates']}
        
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        template = templates[template_name]
        
        # Apply template configuration
        return await update_group_config(group_id, template.config, background_tasks, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying template {template_name} to group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cache/status")
async def get_cache_status(db: Session = Depends(get_db_session)):
    """
    Get configuration cache status
    """
    try:
        # Get cache entries
        cache_entries = db.query(ConfigCache).all()
        
        now = datetime.utcnow()
        active_entries = [entry for entry in cache_entries if not entry.expires_at or entry.expires_at > now]
        expired_entries = [entry for entry in cache_entries if entry.expires_at and entry.expires_at <= now]
        
        return {
            'total_entries': len(cache_entries),
            'active_entries': len(active_entries),
            'expired_entries': len(expired_entries),
            'cache_hit_rate': config_manager.get_cache_hit_rate(),
            'last_cleanup': config_manager.get_last_cleanup_time()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cache/clear")
async def clear_config_cache(
    group_id: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """
    Clear configuration cache (optionally for specific group)
    """
    try:
        if group_id:
            # Clear cache for specific group
            deleted = db.query(ConfigCache).filter(
                ConfigCache.key.like(f"group_config:{group_id}%")
            ).delete()
            db.commit()
            
            logger.info(f"Cleared cache for group {group_id}: {deleted} entries")
            return {'message': f'Cleared cache for group {group_id}', 'entries_cleared': deleted}
        else:
            # Clear all cache
            deleted = db.query(ConfigCache).delete()
            db.commit()
            
            logger.info(f"Cleared all configuration cache: {deleted} entries")
            return {'message': 'Cleared all configuration cache', 'entries_cleared': deleted}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _log_config_change(group_id: str, changes: Dict, db: Session):
    """Log configuration changes to system events"""
    try:
        change_summary = ", ".join([f"{k}: {v['old']} -> {v['new']}" for k, v in changes.items()])
        
        await _log_system_event(
            db,
            'config_changed',
            'group',
            group_id,
            f"Configuration updated: {change_summary}",
            details={'changes': changes}
        )
        
    except Exception as e:
        logger.error(f"Error logging config change: {e}")

async def _log_system_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: str,
    description: str,
    severity: str = 'info',
    details: Dict[str, Any] = None
):
    """Log a system event"""
    try:
        event = SystemEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            severity=severity,
            details=details or {}
        )
        db.add(event)
        db.commit()
        
    except Exception as e:
        logger.error(f"Error logging system event: {e}")

# Include router in main app
def get_config_router():
    """Get the configuration API router"""
    return router
