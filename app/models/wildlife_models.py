# """
# Wildlife Conservation Database Models
# SQLAlchemy models for storing wildlife conservation data
# """

# from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, Integer, Float, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from geoalchemy2 import Geography
# from app.database import Base
# import uuid
# from datetime import datetime, timezone
# from enum import Enum


# class SubmissionStatus(str, Enum):
#     """Status of form submissions"""
#     SUBMITTED = "submitted"
#     VERIFIED = "verified"
#     INVESTIGATING = "investigating"
#     RESOLVED = "resolved"
#     CLOSED = "closed"


# class SyncStatus(str, Enum):
#     """Sync status with Kobo"""
#     PENDING = "pending"
#     SYNCED = "synced"
#     FAILED = "failed"
#     RETRY = "retry"


# class User(Base):
#     """User model for authentication and tracking"""
#     __tablename__ = "users"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     username = Column(String(50), unique=True, nullable=False, index=True)
#     email = Column(String(100), unique=True, nullable=False, index=True)
#     password_hash = Column(String(255), nullable=False)
#     full_name = Column(String(100))
    
#     # Role and permissions
#     role = Column(String(20), default='ranger', nullable=False)  # admin, ranger, analyst, viewer
#     organization = Column(String(100))
#     phone_number = Column(String(20))
    
#     # Location and area of responsibility
#     assigned_area = Column(Geography('POLYGON', srid=4326))  # Geographic area of responsibility
#     base_location = Column(Geography('POINT', srid=4326))    # Home base coordinates
    
#     # Status
#     is_active = Column(Boolean, default=True, nullable=False)
#     is_verified = Column(Boolean, default=False, nullable=False)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     last_login = Column(DateTime(timezone=True))
    
#     # Relationships
#     submissions = relationship("WildlifeSubmission", back_populates="user")


# class FormTemplate(Base):
#     """Kobo form templates cached locally"""
#     __tablename__ = "form_templates"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     kobo_uid = Column(String(100), unique=True, nullable=False, index=True)
    
#     # Form metadata
#     name = Column(String(200), nullable=False)
#     title = Column(String(200))
#     description = Text
#     version = Column(Integer, default=1)
    
#     # Form structure and configuration
#     structure = Column(JSON)  # Parsed form structure for mobile apps
#     raw_kobo_content = Column(JSON)  # Original Kobo form content
    
#     # Status and deployment
#     is_active = Column(Boolean, default=True, nullable=False)
#     is_deployed = Column(Boolean, default=False, nullable=False)
#     deployment_status = Column(String(50))
    
#     # Kobo metadata
#     kobo_owner = Column(String(100))
#     kobo_created_at = Column(DateTime(timezone=True))
#     kobo_modified_at = Column(DateTime(timezone=True))
    
#     # Local timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     last_synced = Column(DateTime(timezone=True))
    
#     # Relationships
#     submissions = relationship("WildlifeSubmission", back_populates="form_template")


# class WildlifeSubmission(Base):
#     """Main table for wildlife incident submissions"""
#     __tablename__ = "wildlife_submissions"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
#     # Form and user references
#     form_template_id = Column(UUID(as_uuid=True), ForeignKey('form_templates.id'), nullable=False)
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
#     # Kobo integration
#     kobo_submission_id = Column(String(100), unique=True, index=True)
#     kobo_form_uid = Column(String(100), nullable=False, index=True)
    
#     # Incident details
#     incident_date = Column(DateTime(timezone=True))
#     incident_time = Column(String(10))  # Time as string for flexibility
    
#     # Location data with spatial indexing
#     location = Column(Geography('POINT', srid=4326))  # GPS coordinates
#     location_accuracy = Column(Float)  # GPS accuracy in meters
#     location_altitude = Column(Float)  # Elevation
#     location_name = Column(String(200))  # Human-readable location
    
#     # Administrative hierarchy
#     administrative_area = Column(JSON)  # Province, district, sector, cell
    
#     # Wildlife information
#     species = Column(String(100), index=True)
#     species_count = Column(Integer, default=1)
#     species_behavior = Column(Text)
    
#     # Incident classification
#     incident_type = Column(String(50), nullable=False, index=True)
#     incident_severity = Column(String(20), default='medium', index=True)  # low, medium, high, critical
#     conflict_type = Column(JSON)  # Multiple conflict types possible
    
#     # Description and details
#     description = Column(Text)
#     circumstances = Column(Text)  # What led to the incident
#     immediate_response = Column(Text)  # What was done immediately
    
#     # Evidence and media
#     photos = Column(JSON)  # Array of photo file paths/URLs
#     videos = Column(JSON)  # Array of video file paths/URLs
#     audio_notes = Column(JSON)  # Array of audio file paths/URLs
#     documents = Column(JSON)  # Additional documents
    
#     # Reporter information
#     reporter_name = Column(String(100))
#     reporter_contact = Column(String(50))
#     reporter_type = Column(String(20))  # ranger, community_member, official, tourist
    
#     # Impact assessment
#     crop_damage_area = Column(Float)  # Hectares of crop damage
#     livestock_lost = Column(Integer)  # Number of livestock lost/injured
#     property_damage_value = Column(Float)  # Estimated monetary damage
#     human_casualties = Column(Integer)  # Number of people injured/killed
    
#     # Response and resolution
#     status = Column(String(20), default=SubmissionStatus.SUBMITTED, nullable=False, index=True)
#     priority = Column(Integer, default=3)  # 1 (highest) to 5 (lowest)
#     assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
#     response_actions = Column(JSON)  # Actions taken in response
#     resolution_details = Column(Text)
#     follow_up_required = Column(Boolean, default=False)
#     follow_up_date = Column(DateTime(timezone=True))
    
#     # Sync status with Kobo
#     sync_status = Column(String(20), default=SyncStatus.PENDING, nullable=False)
#     sync_attempts = Column(Integer, default=0)
#     last_sync_attempt = Column(DateTime(timezone=True))
#     sync_error = Column(Text)
    
#     # Raw form data
#     raw_form_data = Column(JSON, nullable=False)  # Original form submission
#     processed_data = Column(JSON)  # Cleaned and validated data
#     validation_errors = Column(JSON)  # Any validation issues
    
#     # Quality assurance
#     is_verified = Column(Boolean, default=False)
#     verified_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
#     verified_at = Column(DateTime(timezone=True))
#     verification_notes = Column(Text)
    
#     # Metadata
#     submission_source = Column(String(20), default='mobile')  # mobile, web, ussd, sms
#     device_info = Column(JSON)  # Device and app information
#     submission_duration = Column(Integer)  # Time taken to fill form (seconds)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
#     submitted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
#     # Relationships
#     form_template = relationship("FormTemplate", back_populates="submissions")
#     user = relationship("User", back_populates="submissions", foreign_keys=[user_id])
#     assigned_user = relationship("User", foreign_keys=[assigned_to])
#     verified_user = relationship("User", foreign_keys=[verified_by])
#     media_files = relationship("MediaFile", back_populates="submission")


# class MediaFile(Base):
#     """File attachments (photos, videos, audio, documents)"""
#     __tablename__ = "media_files"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     submission_id = Column(UUID(as_uuid=True), ForeignKey('wildlife_submissions.id'), nullable=False)
    
#     # File information
#     filename = Column(String(255), nullable=False)
#     original_filename = Column(String(255))
#     file_path = Column(String(500), nullable=False)  # Path to file on disk/cloud
#     file_url = Column(String(500))  # Public URL if hosted on CDN
    
#     # File metadata
#     file_type = Column(String(50), nullable=False)  # image, video, audio, document
#     mime_type = Column(String(100))
#     file_size = Column(Integer)  # Size in bytes
    
#     # Media-specific metadata
#     image_width = Column(Integer)  # For images
#     image_height = Column(Integer)  # For images
#     duration = Column(Float)  # For audio/video (seconds)
    
#     # GPS data from photo EXIF
#     photo_location = Column(Geography('POINT', srid=4326))
#     photo_taken_at = Column(DateTime(timezone=True))
    
#     # Processing status
#     is_processed = Column(Boolean, default=False)
#     thumbnail_path = Column(String(500))  # Path to thumbnail
#     compressed_path = Column(String(500))  # Path to compressed version
    
#     # Upload information
#     uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
#     upload_method = Column(String(20))  # direct, chunked, resumable
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     # Relationships
#     submission = relationship("WildlifeSubmission", back_populates="media_files")


# class Species(Base):
#     """Reference table for wildlife species"""
#     __tablename__ = "species"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
#     # Species identification
#     common_name = Column(String(100), nullable=False, index=True)
#     scientific_name = Column(String(150), unique=True, index=True)
#     local_names = Column(JSON)  # Local language names
    
#     # Classification
#     category = Column(String(20), nullable=False)  # mammal, bird, reptile, etc.
#     family = Column(String(50))
#     conservation_status = Column(String(50))  # IUCN status
    
#     # Conflict information
#     conflict_risk_level = Column(Integer)  # 1-5 scale
#     typical_conflicts = Column(JSON)  # Types of conflicts this species causes
#     seasonal_patterns = Column(JSON)  # When conflicts are most common
    
#     # Species information
#     description = Column(Text)
#     habitat_info = Column(Text)
#     behavioral_notes = Column(Text)
#     physical_description = Column(Text)
    
#     # Range and distribution
#     geographic_range = Column(Geography('MULTIPOLYGON', srid=4326))
#     habitat_types = Column(JSON)
    
#     # Status
#     is_endangered = Column(Boolean, default=False)
#     is_protected = Column(Boolean, default=False)
#     is_active = Column(Boolean, default=True)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# class ConflictHotspot(Base):
#     """Identified areas with frequent human-wildlife conflicts"""
#     __tablename__ = "conflict_hotspots"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
#     # Location and boundaries
#     name = Column(String(200))
#     center_location = Column(Geography('POINT', srid=4326), nullable=False)
#     hotspot_area = Column(Geography('POLYGON', srid=4326))  # Defined boundary
#     radius_meters = Column(Integer)  # If circular area
    
#     # Analysis results
#     incident_count = Column(Integer, default=0)
#     severity_score = Column(Float)  # Calculated severity
#     risk_level = Column(String(20))  # low, medium, high, critical
    
#     # Dominant patterns
#     dominant_species = Column(String(100))
#     dominant_incident_type = Column(String(50))
#     peak_season = Column(String(20))  # When conflicts peak
#     peak_time = Column(String(20))  # Time of day conflicts peak
    
#     # Contributing factors
#     risk_factors = Column(JSON)  # Environmental and human factors
#     land_use_types = Column(JSON)  # Agriculture, settlement, etc.
#     water_sources_nearby = Column(Boolean, default=False)
    
#     # Mitigation
#     mitigation_measures = Column(JSON)  # Implemented or suggested measures
#     effectiveness_score = Column(Float)  # How well mitigations work
    
#     # Analysis metadata
#     analysis_period_start = Column(DateTime(timezone=True))
#     analysis_period_end = Column(DateTime(timezone=True))
#     analysis_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
#     analyzed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
#     # Status
#     is_active = Column(Boolean, default=True)
#     requires_attention = Column(Boolean, default=False)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# class SyncLog(Base):
#     """Log of synchronization attempts with Kobo"""
#     __tablename__ = "sync_logs"
    
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
#     # Sync details
#     submission_id = Column(UUID(as_uuid=True), ForeignKey('wildlife_submissions.id'))
#     sync_type = Column(String(20), nullable=False)  # form_fetch, data_submit, data_update
#     direction = Column(String(10), nullable=False)  # to_kobo, from_kobo
    
#     # Results
#     status = Column(String(20), nullable=False)  # success, failed, partial
#     error_message = Column(Text)
#     response_data = Column(JSON)  # API response from Kobo
    
#     # Metadata
#     kobo_endpoint = Column(String(200))  # Which Kobo endpoint was called
#     http_status_code = Column(Integer)
#     duration_seconds = Column(Float)
    
#     # Timestamps
#     started_at = Column(DateTime(timezone=True), nullable=False)
#     completed_at = Column(DateTime(timezone=True))
#     created_at = Column(DateTime(timezone=True), server_default=func.now())


# # Create indexes for spatial queries and performance
# from sqlalchemy import Index

# # Spatial indexes
# Index('idx_submissions_location', WildlifeSubmission.location, postgresql_using='gist')
# Index('idx_users_assigned_area', User.assigned_area, postgresql_using='gist')
# Index('idx_users_base_location', User.base_location, postgresql_using='gist')
# Index('idx_hotspots_center', ConflictHotspot.center_location, postgresql_using='gist')
# Index('idx_hotspots_area', ConflictHotspot.hotspot_area, postgresql_using='gist')
# Index('idx_species_range', Species.geographic_range, postgresql_using='gist')
# Index('idx_media_photo_location', MediaFile.photo_location, postgresql_using='gist')

# # Regular indexes for common queries
# Index('idx_submissions_date', WildlifeSubmission.incident_date)
# Index('idx_submissions_status', WildlifeSubmission.status)
# Index('idx_submissions_species', WildlifeSubmission.species)
# Index('idx_submissions_type', WildlifeSubmission.incident_type)
# Index('idx_submissions_sync_status', WildlifeSubmission.sync_status)
# Index('idx_forms_kobo_uid', FormTemplate.kobo_uid)
# Index('idx_media_submission_id', MediaFile.submission_id)