"""
Bot Orchestrator - Central coordinator for managing multiple SpamMonitor instances
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import threading
import multiprocessing
import psutil
import uuid

from ..database.connection import get_database_manager
from ..database.models import Group, GroupConfig, BotInstance, GroupAssignment, SystemEvent
from .spam_monitor_worker import SpamMonitorWorker
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

@dataclass
class WorkerProcess:
    """Represents a worker process running SpamMonitor instances"""
    process: multiprocessing.Process
    instance_id: str
    assigned_groups: Set[str]
    max_groups: int
    started_at: datetime
    last_heartbeat: datetime
    status: str = "starting"

class BotOrchestrator:
    """
    Central orchestrator that manages multiple SpamMonitor worker processes
    and handles group assignments, load balancing, and health monitoring
    """
    
    def __init__(self, max_workers: int = 3, groups_per_worker: int = 5):
        """
        Initialize the Bot Orchestrator
        
        Args:
            max_workers: Maximum number of worker processes to spawn
            groups_per_worker: Maximum groups per worker process
        """
        self.max_workers = max_workers
        self.groups_per_worker = groups_per_worker
        self.workers: Dict[str, WorkerProcess] = {}
        self.db_manager = get_database_manager()
        self.metrics_collector = MetricsCollector()
        
        # Instance identification
        self.instance_name = f"orchestrator-{uuid.uuid4().hex[:8]}"
        self.hostname = psutil.Process().name()
        self.process_id = psutil.Process().pid
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Background tasks
        self.heartbeat_thread = None
        self.health_check_thread = None
        self.assignment_thread = None
        
        logger.info(f"Orchestrator initialized: {self.instance_name}")
    
    async def start(self):
        """Start the orchestrator and all background tasks"""
        logger.info("Starting Bot Orchestrator...")
        
        # Register this orchestrator instance
        await self._register_instance()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.running = True
        
        # Start background threads
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.assignment_thread = threading.Thread(target=self._assignment_loop, daemon=True)
        
        self.heartbeat_thread.start()
        self.health_check_thread.start()
        self.assignment_thread.start()
        
        # Initial group assignment
        await self._assign_groups()
        
        # Log startup event
        await self._log_system_event(
            "orchestrator_started",
            "orchestrator",
            self.instance_name,
            f"Bot Orchestrator started with {self.max_workers} max workers"
        )
        
        logger.info("Bot Orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator and all worker processes"""
        logger.info("Stopping Bot Orchestrator...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop all worker processes
        for worker_id, worker in self.workers.items():
            logger.info(f"Stopping worker {worker_id}")
            if worker.process.is_alive():
                worker.process.terminate()
                worker.process.join(timeout=30)
                if worker.process.is_alive():
                    worker.process.kill()
        
        # Wait for background threads to finish
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        if self.assignment_thread and self.assignment_thread.is_alive():
            self.assignment_thread.join(timeout=5)
        
        # Unregister instance
        await self._unregister_instance()
        
        # Log shutdown event
        await self._log_system_event(
            "orchestrator_stopped",
            "orchestrator",
            self.instance_name,
            "Bot Orchestrator stopped"
        )
        
        logger.info("Bot Orchestrator stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())
    
    async def _register_instance(self):
        """Register this orchestrator instance in the database"""
        try:
            with self.db_manager.get_session() as session:
                instance = BotInstance(
                    instance_name=self.instance_name,
                    hostname=self.hostname,
                    process_id=self.process_id,
                    status='starting',
                    max_groups=self.max_workers * self.groups_per_worker,
                    current_groups=0,
                    version='2.0.0',
                    assigned_groups=[]
                )
                session.add(instance)
                session.commit()
                logger.info(f"Registered orchestrator instance: {self.instance_name}")
        except Exception as e:
            logger.error(f"Failed to register instance: {e}")
            raise
    
    async def _unregister_instance(self):
        """Unregister this orchestrator instance from the database"""
        try:
            with self.db_manager.get_session() as session:
                instance = session.query(BotInstance).filter(
                    BotInstance.instance_name == self.instance_name
                ).first()
                if instance:
                    instance.status = 'stopped'
                    session.commit()
                    logger.info(f"Unregistered orchestrator instance: {self.instance_name}")
        except Exception as e:
            logger.error(f"Failed to unregister instance: {e}")
    
    def _heartbeat_loop(self):
        """Background thread for sending heartbeats"""
        while self.running and not self.shutdown_event.is_set():
            try:
                self._send_heartbeat()
                time.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(5)
    
    def _send_heartbeat(self):
        """Send heartbeat to update instance status"""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage_mb = int(memory.used / 1024 / 1024)
            
            with self.db_manager.get_session() as session:
                instance = session.query(BotInstance).filter(
                    BotInstance.instance_name == self.instance_name
                ).first()
                
                if instance:
                    instance.last_heartbeat = datetime.utcnow()
                    instance.status = 'running'
                    instance.cpu_usage = cpu_usage
                    instance.memory_usage_mb = memory_usage_mb
                    instance.current_groups = len([g for worker in self.workers.values() for g in worker.assigned_groups])
                    instance.assigned_groups = list(set([g for worker in self.workers.values() for g in worker.assigned_groups]))
                    session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    def _health_check_loop(self):
        """Background thread for health checking worker processes"""
        while self.running and not self.shutdown_event.is_set():
            try:
                self._check_worker_health()
                time.sleep(60)  # Health check every minute
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(10)
    
    def _check_worker_health(self):
        """Check health of all worker processes"""
        current_time = datetime.utcnow()
        unhealthy_workers = []
        
        for worker_id, worker in self.workers.items():
            # Check if process is alive
            if not worker.process.is_alive():
                logger.warning(f"Worker {worker_id} process is dead")
                unhealthy_workers.append(worker_id)
                continue
            
            # Check heartbeat timeout (5 minutes)
            if current_time - worker.last_heartbeat > timedelta(minutes=5):
                logger.warning(f"Worker {worker_id} heartbeat timeout")
                unhealthy_workers.append(worker_id)
                continue
            
            # Update worker status
            worker.status = "running"
        
        # Restart unhealthy workers
        for worker_id in unhealthy_workers:
            asyncio.create_task(self._restart_worker(worker_id))
    
    async def _restart_worker(self, worker_id: str):
        """Restart a failed worker process"""
        logger.info(f"Restarting worker {worker_id}")
        
        try:
            old_worker = self.workers.get(worker_id)
            if old_worker:
                # Terminate old process
                if old_worker.process.is_alive():
                    old_worker.process.terminate()
                    old_worker.process.join(timeout=10)
                    if old_worker.process.is_alive():
                        old_worker.process.kill()
                
                # Start new worker with same groups
                assigned_groups = old_worker.assigned_groups.copy()
                del self.workers[worker_id]
                
                await self._start_worker(assigned_groups)
                
                await self._log_system_event(
                    "worker_restarted",
                    "worker",
                    worker_id,
                    f"Worker restarted with {len(assigned_groups)} groups"
                )
                
        except Exception as e:
            logger.error(f"Failed to restart worker {worker_id}: {e}")
    
    def _assignment_loop(self):
        """Background thread for managing group assignments"""
        while self.running and not self.shutdown_event.is_set():
            try:
                asyncio.create_task(self._assign_groups())
                time.sleep(120)  # Check assignments every 2 minutes
            except Exception as e:
                logger.error(f"Assignment loop error: {e}")
                time.sleep(30)
    
    async def _assign_groups(self):
        """Assign groups to worker processes based on load balancing"""
        try:
            with self.db_manager.get_session() as session:
                # Get all active groups
                active_groups = session.query(Group).filter(
                    Group.status == 'active'
                ).all()
                
                if not active_groups:
                    logger.info("No active groups to assign")
                    return
                
                # Get current assignments for this orchestrator
                current_assignments = session.query(GroupAssignment).join(BotInstance).filter(
                    BotInstance.instance_name == self.instance_name
                ).all()
                
                currently_assigned = {assignment.group_id for assignment in current_assignments}
                groups_to_assign = {group.group_id for group in active_groups}
                
                # Find groups that need assignment
                unassigned_groups = groups_to_assign - currently_assigned
                
                # Find groups that should be unassigned
                groups_to_unassign = currently_assigned - groups_to_assign
                
                # Unassign groups that are no longer active
                for group_id in groups_to_unassign:
                    await self._unassign_group(group_id)
                
                # Assign new groups
                for group_id in unassigned_groups:
                    await self._assign_group_to_worker(group_id)
                
                logger.info(f"Group assignment complete: {len(unassigned_groups)} new, {len(groups_to_unassign)} removed")
                
        except Exception as e:
            logger.error(f"Failed to assign groups: {e}")
    
    async def _assign_group_to_worker(self, group_id: str):
        """Assign a group to the best available worker"""
        try:
            # Find worker with least load
            best_worker = None
            min_groups = float('inf')
            
            for worker_id, worker in self.workers.items():
                if len(worker.assigned_groups) < min_groups and len(worker.assigned_groups) < self.groups_per_worker:
                    min_groups = len(worker.assigned_groups)
                    best_worker = worker_id
            
            # If no worker has capacity, start a new one
            if best_worker is None and len(self.workers) < self.max_workers:
                best_worker = await self._start_worker({group_id})
            elif best_worker is None:
                logger.warning(f"No available worker capacity for group {group_id}")
                return
            else:
                # Assign to existing worker
                self.workers[best_worker].assigned_groups.add(group_id)
            
            # Update database
            with self.db_manager.get_session() as session:
                # Get worker instance from database
                instance = session.query(BotInstance).filter(
                    BotInstance.instance_name == self.instance_name
                ).first()
                
                if instance:
                    assignment = GroupAssignment(
                        group_id=group_id,
                        instance_id=instance.id,
                        status='active'
                    )
                    session.add(assignment)
                    session.commit()
                    
                    logger.info(f"Assigned group {group_id} to worker {best_worker}")
            
        except Exception as e:
            logger.error(f"Failed to assign group {group_id}: {e}")
    
    async def _unassign_group(self, group_id: str):
        """Unassign a group from its worker"""
        try:
            # Remove from worker
            for worker_id, worker in self.workers.items():
                if group_id in worker.assigned_groups:
                    worker.assigned_groups.discard(group_id)
                    break
            
            # Update database
            with self.db_manager.get_session() as session:
                assignment = session.query(GroupAssignment).filter(
                    GroupAssignment.group_id == group_id
                ).first()
                
                if assignment:
                    session.delete(assignment)
                    session.commit()
                    
                    logger.info(f"Unassigned group {group_id}")
            
        except Exception as e:
            logger.error(f"Failed to unassign group {group_id}: {e}")
    
    async def _start_worker(self, assigned_groups: Set[str]) -> str:
        """Start a new worker process"""
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create worker process
            process = multiprocessing.Process(
                target=SpamMonitorWorker.run_worker,
                args=(worker_id, assigned_groups, self.instance_name),
                name=f"SpamWorker-{worker_id}"
            )
            
            worker = WorkerProcess(
                process=process,
                instance_id=worker_id,
                assigned_groups=assigned_groups,
                max_groups=self.groups_per_worker,
                started_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                status="starting"
            )
            
            process.start()
            self.workers[worker_id] = worker
            
            logger.info(f"Started worker {worker_id} with {len(assigned_groups)} groups")
            
            await self._log_system_event(
                "worker_started",
                "worker",
                worker_id,
                f"Worker started with groups: {', '.join(assigned_groups)}"
            )
            
            return worker_id
            
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            raise
    
    async def _log_system_event(self, event_type: str, entity_type: str, entity_id: str, description: str, severity: str = "info"):
        """Log a system event to the database"""
        try:
            with self.db_manager.get_session() as session:
                event = SystemEvent(
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    description=description,
                    severity=severity,
                    instance_name=self.instance_name
                )
                session.add(event)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
    
    async def add_group(self, group_id: str, group_name: str, owner_id: str = None, owner_name: str = None) -> bool:
        """Add a new group to be monitored"""
        try:
            with self.db_manager.get_session() as session:
                # Check if group already exists
                existing_group = session.query(Group).filter(Group.group_id == group_id).first()
                if existing_group:
                    logger.warning(f"Group {group_id} already exists")
                    return False
                
                # Create group record
                group = Group(
                    group_id=group_id,
                    group_name=group_name,
                    owner_id=owner_id,
                    owner_name=owner_name,
                    status='active'
                )
                session.add(group)
                
                # Create default configuration
                config = GroupConfig(
                    group_id=group_id
                )
                session.add(config)
                
                session.commit()
                
                await self._log_system_event(
                    "group_added",
                    "group",
                    group_id,
                    f"Group '{group_name}' added to monitoring"
                )
                
                logger.info(f"Added group {group_id} ({group_name}) to monitoring")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add group {group_id}: {e}")
            return False
    
    async def remove_group(self, group_id: str) -> bool:
        """Remove a group from monitoring"""
        try:
            with self.db_manager.get_session() as session:
                group = session.query(Group).filter(Group.group_id == group_id).first()
                if not group:
                    logger.warning(f"Group {group_id} not found")
                    return False
                
                group.status = 'inactive'
                session.commit()
                
                await self._log_system_event(
                    "group_removed",
                    "group",
                    group_id,
                    f"Group '{group.group_name}' removed from monitoring"
                )
                
                logger.info(f"Removed group {group_id} from monitoring")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove group {group_id}: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get orchestrator status information"""
        return {
            'instance_name': self.instance_name,
            'hostname': self.hostname,
            'process_id': self.process_id,
            'running': self.running,
            'workers': {
                worker_id: {
                    'status': worker.status,
                    'assigned_groups': list(worker.assigned_groups),
                    'started_at': worker.started_at.isoformat(),
                    'last_heartbeat': worker.last_heartbeat.isoformat()
                }
                for worker_id, worker in self.workers.items()
            },
            'total_groups': sum(len(worker.assigned_groups) for worker in self.workers.values()),
            'max_capacity': self.max_workers * self.groups_per_worker
        }

async def main():
    """Main function to run the orchestrator"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = BotOrchestrator(max_workers=3, groups_per_worker=5)
    
    try:
        await orchestrator.start()
        
        # Keep running until shutdown
        while orchestrator.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
