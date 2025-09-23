"""Database setup script"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, check_db_connection, check_postgis

def setup_database():
    """Initialize database with required extensions and tables"""
    print("🔧 Setting up Wildlife Conservation Database...")
    
    if not check_db_connection():
        print("❌ Database connection failed")
        print("Check your DATABASE_URL in .env file")
        return False
    
    print("✅ Database connection successful")
    
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    if not check_postgis():
        print("⚠️ PostGIS extension not available")
        print("Enable PostGIS in your Neon dashboard SQL editor:")
        print("CREATE EXTENSION IF NOT EXISTS postgis;")
        return False
    
    print("✅ PostGIS extension available")
    print("🎉 Database setup completed successfully!")
    return True

if __name__ == "__main__":
    setup_database()
