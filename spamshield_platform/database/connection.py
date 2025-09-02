"""
Database connection and session management for SpamShield Platform
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection URL. If None, reads from environment
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        # Try different environment variable patterns
        url = (
            os.getenv('DATABASE_URL') or
            os.getenv('POSTGRES_URL') or
            os.getenv('POSTGRESQL_URL')
        )
        
        if url:
            return url
        
        # Build URL from individual components
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'spamshield')
        username = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with connection pooling"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        
        Usage:
            with db_manager.get_session() as session:
                # Use session here
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session (remember to close it!)"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_engine_info(self) -> dict:
        """Get database engine information"""
        return {
            'url': str(self.engine.url).replace(self.engine.url.password, '***'),
            'driver': self.engine.dialect.name,
            'pool_size': self.engine.pool.size(),
            'checked_out': self.engine.pool.checkedout(),
            'overflow': self.engine.pool.overflow(),
            'checked_in': self.engine.pool.checkedin()
        }

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_db_session():
    """Dependency function for FastAPI to get database sessions"""
    db_manager = get_database_manager()
    session = db_manager.get_session_sync()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """Initialize database with tables and default data"""
    db_manager = get_database_manager()
    
    # Test connection first
    if not db_manager.test_connection():
        raise RuntimeError("Cannot connect to database")
    
    # Create tables
    db_manager.create_tables()
    
    logger.info("Database initialization completed")

if __name__ == "__main__":
    # For testing database connection
    logging.basicConfig(level=logging.INFO)
    
    try:
        db_manager = DatabaseManager()
        if db_manager.test_connection():
            print("✅ Database connection successful")
            print(f"Engine info: {db_manager.get_engine_info()}")
        else:
            print("❌ Database connection failed")
    except Exception as e:
        print(f"❌ Error: {e}")
