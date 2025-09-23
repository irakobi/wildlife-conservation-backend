

"""
Wildlife Conservation App Configuration
Handles environment variables and application settings
"""

import os
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    app_name: str = "Wildlife Conservation API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database - Neon PostgreSQL
    database_url: str = Field(default="")
    database_echo: bool = Field(default=False)
    
    # Kobo API
    kobo_api_token: str = Field(default="")
    kobo_server_url: str = Field(default="https://kf.kobotoolbox.org")
    kobo_timeout: int = Field(default=30)
    
    # Authentication & Security
    secret_key: str = Field(default="")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # CORS - Handle as string or list
    allowed_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8080,http://localhost:4200"
    )
    
    # Redis (for caching and background tasks)
    redis_url: str = Field(default="redis://localhost:6379")
    
    # File uploads
    upload_dir: str = Field(default="./uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_file_types: Union[str, List[str]] = Field(
        default="image/jpeg,image/png,image/webp,video/mp4,audio/wav"
    )
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)
    
    # External services (optional)
    email_from: Optional[str] = Field(default=None)
    smtp_server: Optional[str] = Field(default=None)
    smtp_port: Optional[int] = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    
    # SMS/USSD (optional)
    sms_api_key: Optional[str] = Field(default=None)
    sms_username: Optional[str] = Field(default=None)
    sms_sender_id: Optional[str] = Field(default=None)
    
    # Analytics and monitoring (optional)
    enable_analytics: bool = Field(default=True)
    sentry_dsn: Optional[str] = Field(default=None)
    
    # Background tasks (optional)
    celery_broker_url: Optional[str] = Field(default=None)
    celery_result_backend: Optional[str] = Field(default=None)
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]  # Default fallback
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod  
    def parse_file_types(cls, v):
        """Parse allowed file types from string or list"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["image/jpeg", "image/png"]  # Default fallback
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted"""
        if not v:
            # Allow empty during development
            return v
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL connection string')
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields
    }


# Create settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"⚠️ Warning: Could not load settings from .env file: {e}")
    print("Using default settings. Please check your .env file.")
    # Create with defaults
    settings = Settings(
        database_url="",
        secret_key="development-secret-key-change-in-production",
        kobo_api_token=""
    )


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Development helper functions
def is_development() -> bool:
    """Check if running in development mode"""
    return settings.environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return settings.environment.lower() == "production"


def get_database_url() -> str:
    """Get the database connection URL"""
    return settings.database_url


def get_kobo_config() -> dict:
    """Get Kobo API configuration"""
    return {
        "api_token": settings.kobo_api_token,
        "server_url": settings.kobo_server_url,
        "timeout": settings.kobo_timeout,
    }


def get_cors_config() -> dict:
    """Get CORS configuration"""
    # Ensure allowed_origins is a list
    origins = settings.allowed_origins
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",")]
    
    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["*"],
    }


def validate_critical_settings():
    """Validate that critical settings are provided"""
    errors = []
    
    if not settings.database_url:
        errors.append("DATABASE_URL is required")
    
    if not settings.secret_key or settings.secret_key == "development-secret-key-change-in-production":
        errors.append("SECRET_KEY must be set to a secure value")
    
    if not settings.kobo_api_token:
        errors.append("KOBO_API_TOKEN is required")
    
    if errors and is_production():
        raise ValueError(f"Critical settings missing: {', '.join(errors)}")
    elif errors:
        print(f"⚠️ Warning: {', '.join(errors)}")


# Only validate in production or if explicitly requested
if is_production():
    validate_critical_settings()