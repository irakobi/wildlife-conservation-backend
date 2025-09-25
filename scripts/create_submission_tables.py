# scripts/create_submission_tables.py
"""
Database migration script to create form submission tables
Run this script to set up the submission system tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models.submission_models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_submission_tables():
    """Create all submission-related tables"""
    try:
        # Create engine
        engine = create_engine(settings.database_url)
        
        logger.info("Creating submission tables...")
        
        # Enable PostGIS extension if not already enabled
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            logger.info("PostGIS extension enabled")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created all submission tables:")
        
        # List created tables
        created_tables = [
            "users",
            "form_templates", 
            "form_submissions",
            "media_files",
            "sync_logs"
        ]
        
        for table in created_tables:
            logger.info(f"  ✅ {table}")
        
        # Create indexes for better performance
        with engine.connect() as conn:
            logger.info("Creating indexes...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_submissions_form_id ON form_submissions(form_template_id);",
                "CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON form_submissions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_submissions_sync_status ON form_submissions(sync_status);",
                "CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON form_submissions(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON form_submissions(submitted_at);",
                "CREATE INDEX IF NOT EXISTS idx_media_files_submission_id ON media_files(submission_id);",
                "CREATE INDEX IF NOT EXISTS idx_form_templates_kobo_id ON form_templates(kobo_form_id);",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_sync_logs_created_at ON sync_logs(created_at);"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
                logger.info(f"  ✅ Index created")
            
            conn.commit()
        
        logger.info("Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def verify_tables():
    """Verify that all tables were created correctly"""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if tables exist
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'form_templates', 'form_submissions', 'media_files', 'sync_logs')
            ORDER BY table_name;
            """
            
            result = conn.execute(text(tables_query))
            existing_tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['form_submissions', 'form_templates', 'media_files', 'sync_logs', 'users']
            
            logger.info("Table verification:")
            for table in expected_tables:
                if table in existing_tables:
                    logger.info(f"  ✅ {table} - exists")
                else:
                    logger.error(f"  ❌ {table} - missing")
            
            # Check PostGIS
            postgis_query = "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');"
            result = conn.execute(text(postgis_query))
            postgis_enabled = result.fetchone()[0]
            
            if postgis_enabled:
                logger.info("  ✅ PostGIS extension - enabled")
            else:
                logger.error("  ❌ PostGIS extension - not found")
            
            return len(existing_tables) == len(expected_tables) and postgis_enabled
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration for form submissions...")
    print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    try:
        create_submission_tables()
        
        if verify_tables():
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Update your main.py to include the submission API routes")
            print("2. Test the API endpoints at http://localhost:8000/docs")
            print("3. Start submitting forms from your mobile app")
        else:
            print("\n❌ Migration verification failed!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)