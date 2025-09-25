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