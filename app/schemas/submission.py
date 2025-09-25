# """
# Pydantic schemas for wildlife submission API
# """

# from pydantic import BaseModel, Field, validator
# from typing import Dict, Any, Optional, List
# from datetime import datetime
# from enum import Enum


# class SubmissionStatus(str, Enum):
#     """Status of form submissions"""
#     SUBMITTED = "submitted"
#     VERIFIED = "verified"
#     INVESTIGATING = "investigating"
#     RESOLVED = "resolved"
#     CLOSED = "closed"
#     DELETED = "deleted"


# class IncidentSeverity(str, Enum):
#     """Incident severity levels"""
#     LOW = "low"
#     MEDIUM = "medium"
#     HIGH = "high"
#     CRITICAL = "critical"


# class SubmissionSource(str, Enum):
#     """Source of submission"""
#     MOBILE = "mobile"
#     WEB = "web"
#     USSD = "ussd"
#     SMS = "sms"


# class LocationData(BaseModel):
#     """GPS location data"""
#     latitude: float
#     longitude: float
#     accuracy: Optional[float] = None
#     altitude: Optional[float] = None


# class SubmissionCreate(BaseModel):
#     """Schema for creating new submissions"""
#     form_id: str = Field(..., description="Kobo form UID")
#     data: Dict[str, Any] = Field(..., description="Form submission data")
#     user_id: Optional[str] = Field(None, description="ID of submitting user")
#     submitted_by: Optional[str] = Field(None, description="Name of person submitting")
#     source: Optional[SubmissionSource] = Field(SubmissionSource.MOBILE, description="Submission source")
    
#     @validator('data')
#     def validate_data(cls, v):
#         """Ensure data is not empty"""
#         if not v:
#             raise ValueError("Submission data cannot be empty")
#         return v


# class SubmissionUpdate(BaseModel):
#     """Schema for updating submissions"""
#     status: Optional[SubmissionStatus] = None
#     priority: Optional[int] = Field(None, ge=1, le=5)
#     assigned_to: Optional[str] = None
#     response_actions: Optional[List[str]] = None
#     resolution_details: Optional[str] = None
#     follow_up_required: Optional[bool] = None
#     follow_up_date: Optional[datetime] = None
#     verification_notes: Optional[str] = None


# class SubmissionResponse(BaseModel):
#     """Schema for submission responses"""
#     id: str
#     form_id: str
#     status: SubmissionStatus
#     synced_to_kobo: bool
#     sync_error: Optional[str] = None
    
#     # Timestamps
#     created_at: datetime
#     submitted_at: datetime
#     updated_at: Optional[datetime] = None
    
#     # Incident details
#     incident_date: Optional[datetime] = None
#     location: Optional[LocationData] = None
#     species: Optional[str] = None
#     incident_type: Optional[str] = None
#     description: Optional[str] = None
#     severity: Optional[str] = None
    
#     # Reporter info
#     reporter_name: Optional[str] = None
#     reporter_contact: Optional[str] = None
    
#     # Workflow
#     priority: Optional[int] = None
#     assigned_to: Optional[str] = None
#     verification_status: Optional[bool] = None
#     verification_notes: Optional[str] = None
    
#     # Optional raw data (only included when requested)
#     raw_form_data: Optional[Dict[str, Any]] = None
#     processed_data: Optional[Dict[str, Any]] = None
    
#     class Config:
#         from_attributes = True


# class SubmissionListResponse(BaseModel):
#     """Schema for list of submissions"""
#     submissions: List[SubmissionResponse]
#     count: int
#     limit: int
#     offset: int
#     filters_applied: Dict[str, Any]


# class SubmissionStatistics(BaseModel):
#     """Schema for submission statistics"""
#     total_submissions: int
#     status_breakdown: Dict[str, int]
#     species_breakdown: Dict[str, int]
#     incident_type_breakdown: Dict[str, int]
#     period: Dict[str, Optional[str]]


# class SyncResult(BaseModel):
#     """Schema for sync operation results"""
#     total_attempted: int
#     successful: int
#     failed: int
#     errors: List[Dict[str, str]]


# class MediaFileResponse(BaseModel):
#     """Schema for media file information"""
#     id: str
#     filename: str
#     file_type: str
#     file_size: Optional[int] = None
#     file_url: Optional[str] = None
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

# app/schemas/submission_schemas.py


from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class LocationData(BaseModel):
    """Location information from mobile device"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    altitude: Optional[float] = None

class MediaFileUpload(BaseModel):
    """Media file data for upload"""
    filename: str
    file_type: str
    mime_type: str
    file_size: int
    question_name: str
    file_data: str  # Base64 encoded file data

class FormSubmissionCreate(BaseModel):
    """Schema for creating new form submissions"""
    kobo_form_id: str = Field(..., description="Kobo form identifier")
    submission_data: Dict[str, Any] = Field(..., description="Form answers as JSON")
    username: Optional[str] = None
    device_id: Optional[str] = None
    app_version: Optional[str] = None
    location: Optional[LocationData] = None
    media_files: Optional[List[MediaFileUpload]] = []
    submitted_at: datetime

class FormSubmissionResponse(BaseModel):
    """Response schema for form submissions"""
    id: UUID
    kobo_form_id: str
    status: str
    message: str
    created_at: str

class FormSubmissionList(BaseModel):
    """Paginated list of form submissions"""
    submissions: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int

class FormSubmissionDetail(BaseModel):
    """Detailed form submission"""
    id: UUID
    kobo_form_id: str
    submission_data: Dict[str, Any]
    status: str
    created_at: str

class SyncRequest(BaseModel):
    """Request to sync submissions with Kobo"""
    submission_ids: Optional[List[UUID]] = None
    force_resync: bool = False

class SyncResponse(BaseModel):
    """Response from sync operation"""
    operation_id: UUID
    status: str
    message: str
    submissions_processed: int
    submissions_synced: int
    submissions_failed: int
    started_at: str

class SubmissionStats(BaseModel):
    """Statistics about form submissions"""
    total_submissions: int
    pending_sync: int
    synced: int
    failed_sync: int
    today_submissions: int
    this_week_submissions: int
    forms_with_submissions: int