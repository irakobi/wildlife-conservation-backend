# app/models/submission_models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
from datetime import datetime

from app.database import Base

class FormTemplate(Base):
    """Cached Kobo form templates"""
    __tablename__ = "form_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kobo_form_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    form_structure = Column(JSON)  # Kobo form schema
    version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    submissions = relationship("FormSubmission", back_populates="form_template")

class FormSubmission(Base):
    """Form submissions from mobile apps"""
    __tablename__ = "form_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_template_id = Column(UUID(as_uuid=True), ForeignKey("form_templates.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Submission data
    submission_data = Column(JSON, nullable=False)  # Form answers
    device_id = Column(String)
    app_version = Column(String)
    
    # Location data
    location = Column(Geometry('POINT', srid=4326))
    location_accuracy = Column(Float)
    altitude = Column(Float)
    
    # Timestamps
    submitted_at = Column(DateTime, nullable=False)  # When user submitted
    received_at = Column(DateTime, default=datetime.utcnow)  # When API received
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Sync status
    kobo_submission_id = Column(String)  # ID from Kobo after sync
    sync_status = Column(String, default="pending")  # pending, synced, failed
    sync_attempts = Column(Integer, default=0)
    last_sync_attempt = Column(DateTime)
    sync_error = Column(Text)
    
    # Relationships
    form_template = relationship("FormTemplate", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
    media_files = relationship("MediaFile", back_populates="submission")

class MediaFile(Base):
    """Media files attached to form submissions"""
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("form_submissions.id"), nullable=False)
    
    # File details
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_type = Column(String)  # image, audio, video, document
    mime_type = Column(String)
    file_size = Column(Integer)
    file_path = Column(String)  # Local storage path
    
    # File metadata
    question_name = Column(String)  # Which form question this file answers
    upload_status = Column(String, default="pending")  # pending, uploaded, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("FormSubmission", back_populates="media_files")

class User(Base):
    """Users who submit forms"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True)
    full_name = Column(String)
    organization = Column(String)
    role = Column(String)
    
    # Authentication (basic for now)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    submissions = relationship("FormSubmission", back_populates="user")

class SyncLog(Base):
    """Track sync operations with Kobo"""
    __tablename__ = "sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_type = Column(String, nullable=False)  # form_sync, submission_sync
    status = Column(String, nullable=False)  # success, failed, partial
    
    # Details
    items_processed = Column(Integer, default=0)
    items_success = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_details = Column(JSON)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)