"""
Configuration Manager for Hot-Reload Functionality
Manages configuration caching and real-time updates
"""

import asyncio
import json
import logging
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import threading

from ...database.connection import get_database_manager
from ...database.models import GroupConfig, ConfigCache

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages configuration hot-reloading and caching
    """
    
    def __init__(self, redis_url: str = None):
        """
        Initialize configuration manager
        
        Args:
            redis_url: Redis connection URL for pub/sub notifications
        """
        self.db_manager = get_database_manager()
        self.redis_client = None
        self.pubsub = None
        
        # Initialize Redis if URL provided
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.pubsub = self.redis_client.pubsub()
                logger.info("Redis connection established for config notifications")
            except Exception as e:
                logger.warning(f"Redis connection failed, using database-only mode: {e}")
        
        # In-memory cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_cleanup = datetime.utcnow()
        
        # Background tasks
        self._cleanup_thread = None
        self._notification_thread = None
        self._running = False
        
        logger.info("ConfigManager initialized")
    
    def start(self):
        """Start background tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start cache cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        # Start Redis notification listener if available
        if self.redis_client:
            self._notification_thread = threading.Thread(target=self._notification_loop, daemon=True)
            self._notification_thread.start()
        
        logger.info("ConfigManager background tasks started")
    
    def stop(self):
        """Stop background tasks"""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        if self._notification_thread:
            self._notification_thread.join(timeout=5)
        
        if self.pubsub:
            self.pubsub.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("ConfigManager stopped")
    
    async def get_group_config(self, group_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get group configuration with caching
        
        Args:
            group_id: Group identifier
            use_cache: Whether to use cached values
            
        Returns:
            Configuration dictionary or None if not found
        """
        cache_key = f"group_config:{group_id}"
        
        # Check in-memory cache first
        if use_cache and cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and datetime.utcnow() - cache_time < timedelta(minutes=5):
                self._cache_hits += 1
                return self._cache[cache_key].copy()
        
        # Check database cache
        if use_cache:
            db_cached = await self._get_from_db_cache(cache_key)
            if db_cached:
                self._cache[cache_key] = db_cached
                self._cache_timestamps[cache_key] = datetime.utcnow()
                self._cache_hits += 1
                return db_cached.copy()
        
        # Load from database
        try:
            with self.db_manager.get_session() as session:
                config = session.query(GroupConfig).filter(
                    GroupConfig.group_id == group_id
                ).first()
                
                if not config:
                    self._cache_misses += 1
                    return None
                
                config_dict = config.to_dict()
                
                # Cache the result
                self._cache[cache_key] = config_dict
                self._cache_timestamps[cache_key] = datetime.utcnow()
                
                # Store in database cache
                await self._store_in_db_cache(cache_key, config_dict)
                
                self._cache_misses += 1
                return config_dict.copy()
                
        except Exception as e:
            logger.error(f"Error loading config for group {group_id}: {e}")
            return None
    
    async def notify_config_change(self, group_id: str):
        """
        Notify all instances about configuration change
        
        Args:
            group_id: Group whose configuration changed
        """
        try:
            # Invalidate local cache
            cache_key = f"group_config:{group_id}"
            self._invalidate_cache(cache_key)
            
            # Send Redis notification if available
            if self.redis_client:
                message = {
                    'type': 'config_change',
                    'group_id': group_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                await self._publish_notification('config_changes', message)
            
            # Store notification in database as fallback
            await self._store_notification('config_change', group_id)
            
            logger.info(f"Configuration change notification sent for group {group_id}")
            
        except Exception as e:
            logger.error(f"Error sending config change notification: {e}")
    
    async def reload_all_configs(self):
        """Force reload of all configurations"""
        try:
            # Clear all caches
            self._cache.clear()
            self._cache_timestamps.clear()
            
            # Clear database cache
            with self.db_manager.get_session() as session:
                session.query(ConfigCache).filter(
                    ConfigCache.key.like('group_config:%')
                ).delete()
                session.commit()
            
            # Send reload notification
            if self.redis_client:
                message = {
                    'type': 'reload_all',
                    'timestamp': datetime.utcnow().isoformat()
                }
                await self._publish_notification('config_changes', message)
            
            logger.info("All configurations reloaded")
            
        except Exception as e:
            logger.error(f"Error reloading all configs: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'cached_entries': len(self._cache),
            'last_cleanup': self._last_cleanup.isoformat()
        }
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        total = self._cache_hits + self._cache_misses
        return (self._cache_hits / total * 100) if total > 0 else 0
    
    def get_last_cleanup_time(self) -> str:
        """Get last cleanup time as ISO string"""
        return self._last_cleanup.isoformat()
    
    def _invalidate_cache(self, cache_key: str):
        """Invalidate specific cache entry"""
        self._cache.pop(cache_key, None)
        self._cache_timestamps.pop(cache_key, None)
    
    async def _get_from_db_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get configuration from database cache"""
        try:
            with self.db_manager.get_session() as session:
                cache_entry = session.query(ConfigCache).filter(
                    ConfigCache.key == cache_key
                ).first()
                
                if not cache_entry:
                    return None
                
                # Check if expired
                if cache_entry.expires_at and cache_entry.expires_at <= datetime.utcnow():
                    session.delete(cache_entry)
                    session.commit()
                    return None
                
                return cache_entry.value
                
        except Exception as e:
            logger.error(f"Error getting from database cache: {e}")
            return None
    
    async def _store_in_db_cache(self, cache_key: str, value: Dict[str, Any], ttl_minutes: int = 30):
        """Store configuration in database cache"""
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            with self.db_manager.get_session() as session:
                # Update existing or create new
                cache_entry = session.query(ConfigCache).filter(
                    ConfigCache.key == cache_key
                ).first()
                
                if cache_entry:
                    cache_entry.value = value
                    cache_entry.expires_at = expires_at
                    cache_entry.updated_at = datetime.utcnow()
                else:
                    cache_entry = ConfigCache(
                        key=cache_key,
                        value=value,
                        expires_at=expires_at
                    )
                    session.add(cache_entry)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing in database cache: {e}")
    
    async def _publish_notification(self, channel: str, message: Dict[str, Any]):
        """Publish notification via Redis"""
        try:
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.redis_client.publish,
                    channel,
                    json.dumps(message)
                )
        except Exception as e:
            logger.error(f"Error publishing Redis notification: {e}")
    
    async def _store_notification(self, notification_type: str, group_id: str):
        """Store notification in database as fallback"""
        try:
            cache_key = f"notification:{notification_type}:{group_id}"
            value = {
                'type': notification_type,
                'group_id': group_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self._store_in_db_cache(cache_key, value, ttl_minutes=60)
            
        except Exception as e:
            logger.error(f"Error storing notification in database: {e}")
    
    def _cleanup_loop(self):
        """Background thread for cache cleanup"""
        while self._running:
            try:
                self._cleanup_expired_cache()
                time.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
                time.sleep(60)
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            now = datetime.utcnow()
            expired_keys = []
            
            # Clean in-memory cache (entries older than 10 minutes)
            for key, timestamp in self._cache_timestamps.items():
                if now - timestamp > timedelta(minutes=10):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
            
            # Clean database cache
            with self.db_manager.get_session() as session:
                deleted = session.query(ConfigCache).filter(
                    ConfigCache.expires_at <= now
                ).delete()
                session.commit()
                
                if deleted > 0:
                    logger.debug(f"Cleaned up {deleted} expired cache entries")
            
            self._last_cleanup = now
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def _notification_loop(self):
        """Background thread for Redis notifications"""
        if not self.pubsub:
            return
        
        try:
            self.pubsub.subscribe('config_changes')
            
            while self._running:
                try:
                    message = self.pubsub.get_message(timeout=1)
                    if message and message['type'] == 'message':
                        self._handle_notification(message['data'])
                        
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error in notification loop: {e}")
        finally:
            try:
                self.pubsub.unsubscribe('config_changes')
            except:
                pass
    
    def _handle_notification(self, data):
        """Handle incoming configuration change notifications"""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            message = json.loads(data)
            notification_type = message.get('type')
            
            if notification_type == 'config_change':
                group_id = message.get('group_id')
                if group_id:
                    cache_key = f"group_config:{group_id}"
                    self._invalidate_cache(cache_key)
                    logger.debug(f"Invalidated cache for group {group_id} due to config change")
            
            elif notification_type == 'reload_all':
                self._cache.clear()
                self._cache_timestamps.clear()
                logger.debug("Cleared all cache due to reload_all notification")
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}")

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get or create the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.start()
    return _config_manager
