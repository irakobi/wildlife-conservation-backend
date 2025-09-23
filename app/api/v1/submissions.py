# """
# Submission management endpoints with real database storage
# """

# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from typing import List, Optional, Dict, Any
# from datetime import datetime
# from sqlalchemy.orm import Session
# import logging

# from app.database import get_db
# from app.services.kobo_service import get_kobo_service, KoboService
# from app.services.submission_service import SubmissionService
# from app.models.wildlife_models import WildlifeSubmission, SubmissionStatus
# from app.schemas.submission import (
#     SubmissionCreate, SubmissionResponse, SubmissionListResponse, 
#     SubmissionUpdate, SubmissionStatistics
# )

# router = APIRouter()
# logger = logging.getLogger(__name__)


# @router.post("/", response_model=SubmissionResponse)
# async def create_submission(
#     submission: SubmissionCreate,
#     db: Session = Depends(get_db),
#     kobo_service: KoboService = Depends(get_kobo_service)
# ):
#     """
#     Submit new wildlife incident data
    
#     This endpoint:
#     1. Saves data to your local database (Neon PostgreSQL)
#     2. Attempts to sync to Kobo Toolbox
#     3. Returns submission confirmation
#     """
#     try:
#         submission_service = SubmissionService(db)
        
#         # Create submission in local database
#         logger.info(f"Creating submission for form {submission.form_id}")
#         local_submission = await submission_service.create_submission(
#             form_id=submission.form_id,
#             data=submission.data,
#             user_id=submission.user_id,
#             submitted_by=submission.submitted_by,
#             submission_source=submission.source or "mobile"
#         )
        
#         # Try to sync to Kobo asynchronously
#         kobo_synced = False
#         sync_error = None
        
#         try:
#             # Format data for Kobo submission
#             kobo_response = await kobo_service.submit_data(
#                 submission.form_id, 
#                 submission.data
#             )
            
#             if kobo_response:
#                 # Mark as synced
#                 await submission_service.mark_synced(
#                     str(local_submission.id),
#                     kobo_response.get('id')
#                 )
#                 kobo_synced = True
#                 logger.info(f"Submission {local_submission.id} synced to Kobo")
            
#         except Exception as sync_error_detail:
#             # Log sync failure but don't fail the submission
#             await submission_service.mark_sync_failed(
#                 str(local_submission.id),
#                 str(sync_error_detail)
#             )
#             sync_error = str(sync_error_detail)
#             logger.warning(f"Kobo sync failed for {local_submission.id}: {sync_error}")
        
#         # Return response
#         return SubmissionResponse(
#             id=str(local_submission.id),
#             form_id=local_submission.kobo_form_uid,
#             status=local_submission.status,
#             synced_to_kobo=kobo_synced,
#             sync_error=sync_error,
#             created_at=local_submission.created_at,
#             submitted_at=local_submission.submitted_at,
#             incident_date=local_submission.incident_date,
#             location=_format_location(local_submission.location),
#             species=local_submission.species,
#             incident_type=local_submission.incident_type,
#             description=local_submission.description
#         )
        
#     except Exception as e:
#         logger.error(f"Failed to create submission: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create submission: {str(e)}"
#         )


# @router.get("/", response_model=SubmissionListResponse)
# async def get_submissions(
#     form_id: Optional[str] = Query(None, description="Filter by form ID"),
#     user_id: Optional[str] = Query(None, description="Filter by user ID"),
#     status: Optional[str] = Query(None, description="Filter by status"),
#     species: Optional[str] = Query(None, description="Filter by species"),
#     incident_type: Optional[str] = Query(None, description="Filter by incident type"),
#     date_from: Optional[datetime] = Query(None, description="Start date filter"),
#     date_to: Optional[datetime] = Query(None, description="End date filter"),
#     lat: Optional[float] = Query(None, description="Latitude for location filter"),
#     lng: Optional[float] = Query(None, description="Longitude for location filter"),
#     radius_km: Optional[float] = Query(10.0, description="Search radius in kilometers"),
#     limit: int = Query(50, ge=1, le=100, description="Number of results"),
#     offset: int = Query(0, ge=0, description="Result offset"),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get submitted wildlife data with filtering options
    
#     Supports filtering by:
#     - Form ID
#     - User ID  
#     - Status (submitted, verified, resolved, etc.)
#     - Species
#     - Date range
#     - Geographic location (within radius)
#     """
#     try:
#         submission_service = SubmissionService(db)
        
#         # Build location filter
#         location_filter = None
#         if lat is not None and lng is not None:
#             location_filter = {
#                 'lat': lat,
#                 'lng': lng,
#                 'radius_meters': radius_km * 1000  # Convert km to meters
#             }
        
#         # Get submissions
#         submissions = await submission_service.get_submissions(
#             form_id=form_id,
#             user_id=user_id,
#             status=status,
#             species=species,
#             location_filter=location_filter,
#             date_from=date_from,
#             date_to=date_to,
#             limit=limit,
#             offset=offset
#         )
        
#         # Convert to response format
#         submission_responses = []
#         for sub in submissions:
#             submission_responses.append(SubmissionResponse(
#                 id=str(sub.id),
#                 form_id=sub.kobo_form_uid,
#                 status=sub.status,
#                 synced_to_kobo=sub.sync_status == "synced",
#                 created_at=sub.created_at,
#                 submitted_at=sub.submitted_at,
#                 incident_date=sub.incident_date,
#                 location=_format_location(sub.location),
#                 species=sub.species,
#                 incident_type=sub.incident_type,
#                 description=sub.description,
#                 reporter_name=sub.reporter_name,
#                 severity=sub.incident_severity
#             ))
        
#         return SubmissionListResponse(
#             submissions=submission_responses,
#             count=len(submission_responses),
#             limit=limit,
#             offset=offset,
#             filters_applied={
#                 "form_id": form_id,
#                 "status": status,
#                 "species": species,
#                 "location_filter": location_filter is not None,
#                 "date_range": date_from is not None or date_to is not None
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Failed to get submissions: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve submissions: {str(e)}"
#         )


# @router.get("/{submission_id}", response_model=SubmissionResponse)
# async def get_submission(
#     submission_id: str,
#     include_raw_data: bool = Query(False, description="Include raw form data"),
#     db: Session = Depends(get_db)
# ):
#     """Get specific submission by ID with optional raw data"""
#     try:
#         submission_service = SubmissionService(db)
#         submission = await submission_service.get_submission_by_id(submission_id)
        
#         if not submission:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Submission not found: {submission_id}"
#             )
        
#         response = SubmissionResponse(
#             id=str(submission.id),
#             form_id=submission.kobo_form_uid,
#             status=submission.status,
#             synced_to_kobo=submission.sync_status == "synced",
#             created_at=submission.created_at,
#             submitted_at=submission.submitted_at,
#             incident_date=submission.incident_date,
#             location=_format_location(submission.location),
#             species=submission.species,
#             incident_type=submission.incident_type,
#             description=submission.description,
#             reporter_name=submission.reporter_name,
#             severity=submission.incident_severity,
#             priority=submission.priority,
#             assigned_to=str(submission.assigned_to) if submission.assigned_to else None,
#             verification_status=submission.is_verified,
#             verification_notes=submission.verification_notes
#         )
        
#         # Include raw data if requested
#         if include_raw_data:
#             response.raw_form_data = submission.raw_form_data
#             response.processed_data = submission.processed_data
        
#         return response
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to get submission {submission_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to retrieve submission: {str(e)}"
#         )


# @router.put("/{submission_id}", response_model=SubmissionResponse)
# async def update_submission(
#     submission_id: str,
#     updates: SubmissionUpdate,
#     db: Session = Depends(get_db)
# ):
#     """Update an existing submission (for workflow management)"""
#     try:
#         submission_service = SubmissionService(db)
        
#         # Convert updates to dict, excluding None values
#         update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
        
#         updated_submission = await submission_service.update_submission(
#             submission_id, 
#             update_data
#         )
        
#         if not updated_submission:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Submission not found: {submission_id}"
#             )
        
#         return SubmissionResponse(
#             id=str(updated_submission.id),
#             form_id=updated_submission.kobo_form_uid,
#             status=updated_submission.status,
#             synced_to_kobo=updated_submission.sync_status == "synced",
#             created_at=updated_submission.created_at,
#             submitted_at=updated_submission.submitted_at,
#             incident_date=updated_submission.incident_date,
#             location=_format_location(updated_submission.location),
#             species=updated_submission.species,
#             incident_type=updated_submission.incident_type,
#             description=updated_submission.description,
#             priority=updated_submission.priority,
#             assigned_to=str(updated_submission.assigned_to) if updated_submission.assigned_to else None
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to update submission {submission_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update submission: {str(e)}"
#         )


# @router.delete("/{submission_id}")
# async def delete_submission(
#     submission_id: str,
#     db: Session = Depends(get_db)
# ):
#     """Delete a submission (admin only)"""
#     try:
#         submission_service = SubmissionService(db)
#         submission = await submission_service.get_submission_by_id(submission_id)
        
#         if not submission:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Submission not found: {submission_id}"
#             )
        
#         # Mark as deleted rather than hard delete to preserve data integrity
#         await submission_service.update_submission(
#             submission_id,
#             {"status": "deleted"}
#         )
        
#         return {"message": f"Submission {submission_id} deleted successfully"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to delete submission {submission_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete submission: {str(e)}"
#         )


# @router.post("/sync", )
# async def sync_pending_submissions(
#     limit: int = Query(10, ge=1, le=50, description="Max submissions to sync"),
#     db: Session = Depends(get_db),
#     kobo_service: KoboService = Depends(get_kobo_service)
# ):
#     """Manually trigger sync of pending submissions to Kobo"""
#     try:
#         submission_service = SubmissionService(db)
        
#         # Get pending submissions
#         pending_submissions = await submission_service.get_pending_syncs(limit)
        
#         sync_results = {
#             "total_attempted": len(pending_submissions),
#             "successful": 0,
#             "failed": 0,
#             "errors": []
#         }
        
#         for submission in pending_submissions:
#             try:
#                 # Attempt sync to Kobo
#                 kobo_response = await kobo_service.submit_data(
#                     submission.kobo_form_uid,
#                     submission.raw_form_data
#                 )
                
#                 if kobo_response:
#                     await submission_service.mark_synced(
#                         str(submission.id),
#                         kobo_response.get('id')
#                     )
#                     sync_results["successful"] += 1
#                 else:
#                     await submission_service.mark_sync_failed(
#                         str(submission.id),
#                         "No response from Kobo API"
#                     )
#                     sync_results["failed"] += 1
                    
#             except Exception as sync_error:
#                 await submission_service.mark_sync_failed(
#                     str(submission.id),
#                     str(sync_error)
#                 )
#                 sync_results["failed"] += 1
#                 sync_results["errors"].append({
#                     "submission_id": str(submission.id),
#                     "error": str(sync_error)
#                 })
        
#         return sync_results
        
#     except Exception as e:
#         logger.error(f"Failed to sync submissions: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to sync submissions: {str(e)}"
#         )


# @router.get("/statistics/summary", response_model=SubmissionStatistics)
# async def get_submission_statistics(
#     date_from: Optional[datetime] = Query(None, description="Start date for statistics"),
#     date_to: Optional[datetime] = Query(None, description="End date for statistics"),
#     db: Session = Depends(get_db)
# ):
#     """Get statistics about wildlife submissions"""
#     try:
#         submission_service = SubmissionService(db)
        
#         stats = await submission_service.get_submission_statistics(
#             date_from=date_from,
#             date_to=date_to
#         )
        
#         return SubmissionStatistics(**stats)
        
#     except Exception as e:
#         logger.error(f"Failed to get statistics: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get statistics: {str(e)}"
#         )


# def _format_location(location_wkb) -> Optional[Dict[str, float]]:
#     """Format PostGIS location data for API response"""
#     if not location_wkb:
#         return None
    
#     try:
#         from geoalchemy2.shape import to_shape
#         point = to_shape(location_wkb)
#         return {
#             "latitude": point.y,
#             "longitude": point.x
#         }
#     except Exception as e:
#         logger.warning(f"Failed to format location: {e}")
#         return None