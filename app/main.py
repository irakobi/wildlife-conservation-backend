"""
Wildlife Conservation FastAPI Application
Main entry point for the API server
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uuid

from app.config import settings, get_cors_config
from app.database import startup_db, shutdown_db
from app.api.v1.api import api_router
from app.core.exceptions import WildlifeConservationException

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🦁 Starting Wildlife Conservation API...")
    await startup_db()
    logger.info(f"🌍 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"🔑 Kobo server: {settings.kobo_server_url}")
    yield
    # Shutdown
    logger.info("🦁 Shutting down Wildlife Conservation API...")
    await shutdown_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    🦁 **Wildlife Conservation Data Collection API**
    
    A comprehensive API for managing wildlife conservation data collection through Kobo Toolbox integration.
    
    ## Features
    
    * 📋 **Form Management**: Fetch and manage Kobo forms
    * 📊 **Data Collection**: Submit and manage wildlife incident reports
    * 🗺️ **Spatial Data**: GPS coordinates and mapping support
    * 👥 **User Management**: Authentication and role-based access
    * 📈 **Analytics**: Wildlife conflict analysis and reporting
    * 🔄 **Synchronization**: Bi-directional sync with Kobo Toolbox
    
    ## Authentication
    
    Most endpoints require authentication using JWT tokens. Get your token from `/api/v1/auth/login`.
    
    ## Rate Limits
    
    API requests are rate-limited to prevent abuse. Check response headers for limit information.
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Trust proxy headers in production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure with actual domains in production
    )

# CORS middleware
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to response"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )
    
    return response


# Custom exception handlers
@app.exception_handler(WildlifeConservationException)
async def wildlife_exception_handler(request: Request, exc: WildlifeConservationException):
    """Handle custom wildlife conservation exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "WildlifeConservationError",
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPError",
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors"""
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Internal server error (Request ID: {request_id}): {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal server error occurred",
                "request_id": request_id
            }
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🦁 Wildlife Conservation API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "status": "operational"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "environment": settings.environment
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Add this endpoint to your main.py after the health_check function
@app.get("/api/v1/status", tags=["API"])  
async def api_status():
    """API status endpoint"""
    return {
        "api_name": settings.app_name,
        "version": settings.app_version,
        "status": "running", 
        "environment": settings.environment,
        "endpoints": {
            "health": "/health",
            "forms": "/api/v1/forms/",
            "submissions": "/api/v1/submissions/"
        }
    }

# Startup message
@app.on_event("startup")
async def startup_message():
    """Display startup information"""
    logger.info("=" * 60)
    logger.info(f"🦁 {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Environment: {settings.environment}")
    logger.info(f"🏠 Host: {settings.host}:{settings.port}")
    logger.info(f"📚 Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔑 Kobo Integration: {settings.kobo_server_url}")
    logger.info("=" * 60)


# For development server
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )