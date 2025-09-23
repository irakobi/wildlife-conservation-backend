#!/usr/bin/env python3
"""
Wildlife Conservation API Server Launcher
Simple script to start the FastAPI server
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🦁 Starting Wildlife Conservation API Server...")
    print(f"Environment: {settings.environment}")
    print(f"Host: {settings.host}:{settings.port}")
    print(f"Debug: {settings.debug}")
    print(f"Documentation: http://{settings.host}:{settings.port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
