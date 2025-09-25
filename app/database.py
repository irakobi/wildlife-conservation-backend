"""
Database connection and session management for Wildlife Conservation App
Uses SQLAlchemy with Neon PostgreSQL and PostGIS support
"""

import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from geoalchemy2 import Geometry

from app.config import settings
# from app.models.submission_models import Base as SubmissionBase, FormSubmission, FormTemplate, MediaFile, User, SyncLog



# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,  # Log SQL queries in debug mode
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
    connect_args={
        "sslmode": "require",  # Required for Neon
        "application_name": "wildlife-conservation-api",
    }
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base for models
Base = declarative_base()

# Naming convention for consistent constraint names
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Use this in FastAPI endpoints with Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for non-FastAPI usage
    Remember to close the session when done
    """
    return SessionLocal()


def init_db() -> None:
    """Initialize the database with extensions and basic setup"""
    try:
        with engine.begin() as connection:
            logger.info("Initializing database...")
            
            # Enable PostGIS extension for spatial data
            logger.info("Enabling PostGIS extension...")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            
            # Enable UUID extension for generating UUIDs
            logger.info("Enabling UUID extension...")
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            
            # Enable trigram extension for text search
            logger.info("Enabling pg_trgm extension...")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            
            # Enable hstore for key-value storage
            logger.info("Enabling hstore extension...")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS hstore;"))
            
            logger.info("Database extensions enabled successfully")
            
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            # Test basic connection
            result = connection.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                logger.info("Database connection successful")
                return True
            return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def check_postgis() -> bool:
    """Check if PostGIS extension is available"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT PostGIS_Version();"))
            version = result.fetchone()[0]
            logger.info(f"PostGIS version: {version}")
            return True
    except Exception as e:
        logger.error(f"PostGIS check failed: {e}")
        return False


def get_db_info() -> dict:
    """Get database information for health checks"""
    try:
        with engine.connect() as connection:
            # Get PostgreSQL version
            pg_version = connection.execute(text("SELECT version();")).fetchone()[0]
            
            # Get PostGIS version
            try:
                postgis_version = connection.execute(text("SELECT PostGIS_Version();")).fetchone()[0]
            except:
                postgis_version = "Not installed"
            
            # Get database name
            db_name = connection.execute(text("SELECT current_database();")).fetchone()[0]
            
            # Get connection count
            conn_count = connection.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();")
            ).fetchone()[0]
            
            return {
                "postgresql_version": pg_version,
                "postgis_version": postgis_version,
                "database_name": db_name,
                "active_connections": conn_count,
                "status": "healthy"
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def create_spatial_index(table_name: str, column_name: str) -> None:
    """Create a spatial index on a geometry column"""
    try:
        with engine.begin() as connection:
            index_name = f"idx_{table_name}_{column_name}_gist"
            sql = text(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name} 
                USING GIST ({column_name});
            """)
            connection.execute(sql)
            logger.info(f"Created spatial index: {index_name}")
    except Exception as e:
        logger.error(f"Failed to create spatial index: {e}")
        raise


def create_text_search_index(table_name: str, column_name: str) -> None:
    """Create a full-text search index on a text column"""
    try:
        with engine.begin() as connection:
            index_name = f"idx_{table_name}_{column_name}_gin"
            sql = text(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name} 
                USING GIN (to_tsvector('english', {column_name}));
            """)
            connection.execute(sql)
            logger.info(f"Created text search index: {index_name}")
    except Exception as e:
        logger.error(f"Failed to create text search index: {e}")
        raise


def execute_sql_file(file_path: str) -> None:
    """Execute SQL statements from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        with engine.begin() as connection:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    connection.execute(text(statement))
        
        logger.info(f"Successfully executed SQL file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to execute SQL file {file_path}: {e}")
        raise


def backup_database(backup_path: str) -> None:
    """Create a database backup (requires pg_dump)"""
    import subprocess
    import os
    from urllib.parse import urlparse
    
    try:
        # Parse database URL
        parsed = urlparse(settings.database_url)
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port),
            '-U', parsed.username,
            '-d', parsed.path.lstrip('/'),
            '--no-password',
            '--verbose',
            '-f', backup_path
        ]
        
        subprocess.run(cmd, env=env, check=True)
        logger.info(f"Database backup created: {backup_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise


class DatabaseManager:
    """Database management utilities"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("All tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All tables dropped")
    
    def reset_database(self):
        """Reset database (drop and recreate tables)"""
        logger.warning("Resetting database...")
        self.drop_tables()
        self.create_tables()
        init_db()
        logger.info("Database reset completed")
    
    def get_table_info(self) -> dict:
        """Get information about database tables"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT 
                        table_name,
                        table_type
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
                
                tables = [{"name": row[0], "type": row[1]} for row in result]
                
                return {
                    "tables": tables,
                    "table_count": len(tables)
                }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {"error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()


# Startup/shutdown event handlers for FastAPI
async def startup_db():
    """Database startup tasks"""
    logger.info("Starting database connection...")
    
    if not check_db_connection():
        raise Exception("Failed to connect to database")
    
    if not check_postgis():
        logger.warning("PostGIS extension not available - spatial features may not work")
    
    # Initialize database if needed
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    logger.info("Database startup completed successfully")


async def shutdown_db():
    """Database shutdown tasks"""
    logger.info("Shutting down database connection...")
    engine.dispose()
    logger.info("Database shutdown completed")


# Dependency for getting async database session (if needed later)
async def get_async_db():
    """Placeholder for async database session (can be implemented later)"""
    # This would require asyncpg and async SQLAlchemy setup
    # For now, we're using sync sessions which work fine with FastAPI
    pass