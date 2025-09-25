# app/api/v1/submissions.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.services.submission_service import SubmissionService
from app.services.kobo_service import KoboService
from app.schemas.submission_schemas import (
    FormSubmissionCreate,
    FormSubmissionResponse,
    FormSubmissionDetail,
    FormSubmissionList,
    SyncRequest,
    SyncResponse,
    SubmissionStats
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_submission_service(db: Session = Depends(get_db)) -> SubmissionService:
    """Dependency to get submission service"""
    kobo_service = KoboService()
    return SubmissionService(db, kobo_service)

@router.post("/", response_model=FormSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    submission_data: FormSubmissionCreate,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Submit a completed Kobo form
    
    Creates a new form submission and attempts to sync with Kobo Toolbox.
    Supports media file uploads and location data.
    """
    try:
        submission = await service.create_submission(submission_data)
        return submission
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission"
        )

@router.get("/", response_model=FormSubmissionList)
async def get_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    form_id: Optional[str] = Query(None, description="Filter by Kobo form ID"),
    sync_status: Optional[str] = Query(None, description="Filter by sync status", regex="^(pending|synced|failed)$"),
    username: Optional[str] = Query(None, description="Filter by username"),
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Get paginated list of form submissions
    
    Supports filtering by form ID, sync status, and username.
    Returns submissions ordered by creation date (newest first).
    """
    try:
        result = await service.get_submissions(
            page=page,
            per_page=per_page,
            form_id=form_id,
            sync_status=sync_status,
            username=username
        )
        return FormSubmissionList(**result)
    except Exception as e:
        logger.error(f"Failed to get submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submissions"
        )

@router.get("/{submission_id}", response_model=FormSubmissionDetail)
async def get_submission(
    submission_id: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Get detailed information about a specific submission
    
    Returns submission data, media files, and sync status.
    """
    try:
        submission = await service.get_submission(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        return submission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission"
        )

@router.post("/sync", response_model=SyncResponse)
async def sync_submissions(
    sync_request: SyncRequest = SyncRequest(),
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Manually trigger sync with Kobo Toolbox
    
    Syncs pending submissions or specific submissions with Kobo.
    Use force_resync=true to retry failed syncs immediately.
    """
    try:
        result = await service.sync_submissions(sync_request)
        return SyncResponse(**result)
    except Exception as e:
        logger.error(f"Failed to sync submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync submissions"
        )

@router.get("/stats/overview", response_model=SubmissionStats)
async def get_submission_stats(
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Get submission statistics and overview
    
    Returns counts of total, pending, synced, and failed submissions.
    Includes daily and weekly submission counts.
    """
    try:
        stats = await service.get_submission_stats()
        return SubmissionStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get submission stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Delete a form submission
    
    Removes the submission and associated media files.
    Note: This does not remove data from Kobo if already synced.
    """
    try:
        success = await service.delete_submission(submission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete submission"
        )

@router.get("/{submission_id}/media/{media_id}")
async def download_media_file(
    submission_id: UUID,
    media_id: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Download a media file from a submission
    
    Returns the actual file content for images, audio, video, or documents.
    """
    try:
        file_response = await service.get_media_file(submission_id, media_id)
        if not file_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )
        return file_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download media file {media_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download media file"
        )

@router.post("/{submission_id}/resync")
async def resync_submission(
    submission_id: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Retry syncing a specific submission
    
    Forces a resync attempt for a failed or pending submission.
    """
    try:
        result = await service.resync_single_submission(submission_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        return {"message": "Resync initiated", "submission_id": submission_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resync submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resync submission"
        )