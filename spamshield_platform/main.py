"""
SpamShield Platform - Main Entry Point
Robust multi-group spam monitoring platform
"""

import asyncio
import logging
import os
import sys
import signal
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spamshield_platform.database.connection import init_database, get_database_manager
from spamshield_platform.orchestrator.bot_orchestrator import BotOrchestrator
from spamshield_platform.api.configuration.config_api import get_config_router
from spamshield_platform.api.group_management.group_api import get_group_router
from spamshield_platform.api.metrics.metrics_api import get_metrics_router
from spamshield_platform.orchestrator.metrics_collector import get_metrics_collector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('spamshield_platform/logs/spamshield.log')
    ]
)

logger = logging.getLogger(__name__)

# Global instances
orchestrator: BotOrchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator
    
    logger.info("Starting SpamShield Platform...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Start metrics collector
        logger.info("Starting metrics collector...")
        metrics_collector = get_metrics_collector()
        
        # Initialize and start orchestrator
        logger.info("Starting bot orchestrator...")
        orchestrator = BotOrchestrator(
            max_workers=int(os.getenv('MAX_WORKERS', '3')),
            groups_per_worker=int(os.getenv('GROUPS_PER_WORKER', '5'))
        )
        await orchestrator.start()
        
        logger.info("SpamShield Platform started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down SpamShield Platform...")
        
        if orchestrator:
            await orchestrator.stop()
        
        if 'metrics_collector' in locals():
            metrics_collector.stop()
        
        logger.info("SpamShield Platform shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SpamShield Platform",
    description="Robust multi-group spam monitoring platform for GroupMe",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(get_config_router(), prefix="/api/v1")
app.include_router(get_group_router(), prefix="/api/v1")
app.include_router(get_metrics_router(), prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SpamShield Platform",
        "version": "2.0.0",
        "description": "Robust multi-group spam monitoring platform",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_manager = get_database_manager()
        db_healthy = db_manager.test_connection()
        
        # Check orchestrator status
        orchestrator_status = orchestrator.get_status() if orchestrator else {"status": "not_started"}
        
        # Get metrics collector status
        metrics_collector = get_metrics_collector()
        metrics_stats = {"status": "running" if metrics_collector else "not_started"}
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "orchestrator": orchestrator_status.get("running", False),
                "metrics_collector": "healthy" if metrics_collector else "unhealthy"
            },
            "orchestrator": orchestrator_status,
            "metrics": metrics_stats
        }
        
        status_code = 200 if db_healthy else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            },
            status_code=503
        )

@app.get("/status")
async def platform_status():
    """Detailed platform status"""
    try:
        # Get orchestrator status
        orchestrator_status = orchestrator.get_status() if orchestrator else {}
        
        # Get metrics summary
        metrics_collector = get_metrics_collector()
        platform_summary = metrics_collector.get_platform_summary() if metrics_collector else {}
        
        # Get database info
        db_manager = get_database_manager()
        db_info = db_manager.get_engine_info()
        
        return {
            "platform": {
                "name": "SpamShield Platform",
                "version": "2.0.0",
                "uptime": orchestrator_status.get("uptime", "unknown"),
                "status": "operational"
            },
            "orchestrator": orchestrator_status,
            "metrics": platform_summary,
            "database": db_info
        }
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/reload")
async def reload_platform():
    """Reload platform configuration and restart services"""
    try:
        logger.info("Platform reload requested")
        
        # Reload configurations
        from platform.api.configuration.config_manager import get_config_manager
        config_manager = get_config_manager()
        await config_manager.reload_all_configs()
        
        # Restart orchestrator (if needed)
        # This could be implemented to gracefully restart workers
        
        return {"message": "Platform reload initiated", "status": "success"}
        
    except Exception as e:
        logger.error(f"Platform reload error: {e}")
        raise HTTPException(status_code=500, detail="Reload failed")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    # FastAPI will handle graceful shutdown via lifespan

# Set up signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("spamshield_platform/logs", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "spamshield_platform.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        workers=1,  # Use 1 worker for now due to shared state
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
