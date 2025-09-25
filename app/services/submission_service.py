# app/services/submission_service.py
import os
import uuid
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from geoalchemy2.functions import ST_MakePoint

from app.models.submission_models import FormSubmission, FormTemplate, MediaFile, User, SyncLog
from app.schemas.submission_schemas import FormSubmissionCreate, LocationData, MediaFileUpload
from app.services.kobo_service import KoboService
import logging

logger = logging.getLogger(__name__)

class SubmissionService:
    def __init__(self, db: Session, kobo_service: KoboService):
        self.db = db
        self.kobo_service = kobo_service
        self.media_storage_path = "storage/media"
        os.makedirs(self.media_storage_path, exist_ok=True)

    async def create_submission(self, submission_data: FormSubmissionCreate) -> Dict[str, Any]:
        """Create a new form submission and save to database"""
        try:
            # Get or create form template
            form_template = await self._get_or_create_form_template(submission_data.kobo_form_id)
            
            # Get or create user
            user = None
            if submission_data.username:
                user = await self._get_or_create_user(submission_data.username)
            
            # Create submission record
            submission = FormSubmission(
                form_template_id=form_template.id,
                user_id=user.id if user else None,
                submission_data=submission_data.submission_data,
                device_id=submission_data.device_id,
                app_version=submission_data.app_version,
                submitted_at=submission_data.submitted_at,
                sync_status="pending"
            )
            
            # Add location if provided
            if submission_data.location:
                submission.location = ST_MakePoint(
                    submission_data.location.longitude,
                    submission_data.location.latitude
                )
                submission.location_accuracy = submission_data.location.accuracy
                submission.altitude = submission_data.location.altitude
            
            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)
            
            # Handle media files
            if submission_data.media_files:
                await self._save_media_files(submission.id, submission_data.media_files)
            
            logger.info(f"Created submission {submission.id} for form {submission_data.kobo_form_id}")
            
            return {
                "id": submission.id,
                "kobo_form_id": submission_data.kobo_form_id,
                "status": "received",
                "message": "Submission saved successfully",
                "created_at": submission.created_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create submission: {e}")
            import traceback
            logger.error(f"Create submission traceback: {traceback.format_exc()}")
            raise

    async def get_submissions(self, **kwargs) -> Dict[str, Any]:
        """Get paginated list of submissions"""
        try:
            page = kwargs.get("page", 1)
            per_page = kwargs.get("per_page", 20)
            form_id = kwargs.get("form_id")
            sync_status = kwargs.get("sync_status")
            username = kwargs.get("username")
            
            query = self.db.query(FormSubmission).join(FormTemplate)
            
            # Apply filters
            if form_id:
                query = query.filter(FormTemplate.kobo_form_id == form_id)
            if sync_status:
                query = query.filter(FormSubmission.sync_status == sync_status)
            if username:
                query = query.join(User).filter(User.username == username)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            submissions = query.order_by(desc(FormSubmission.created_at)).offset(
                (page - 1) * per_page
            ).limit(per_page).all()
            
            return {
                "submissions": [self._to_response_dict(sub) for sub in submissions],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get submissions: {e}")
            import traceback
            logger.error(f"Get submissions traceback: {traceback.format_exc()}")
            raise

    async def get_submission(self, submission_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get submission by ID"""
        try:
            submission = self.db.query(FormSubmission).filter(
                FormSubmission.id == submission_id
            ).first()
            
            if not submission:
                return None
            
            # Get media files
            media_files = self.db.query(MediaFile).filter(
                MediaFile.submission_id == submission_id
            ).all()
            
            result = {
                "id": submission.id,
                "kobo_form_id": submission.form_template.kobo_form_id,
                "submission_data": submission.submission_data,
                "status": submission.sync_status,
                "created_at": submission.created_at.isoformat(),
                "submitted_at": submission.submitted_at.isoformat(),
                "username": submission.user.username if submission.user else None,
                "device_id": submission.device_id,
                "media_files": [self._media_file_to_dict(mf) for mf in media_files]
            }
            
            # Add location if available
            if submission.location:
                from sqlalchemy import func
                coords = self.db.query(
                    func.ST_X(submission.location).label('longitude'),
                    func.ST_Y(submission.location).label('latitude')
                ).first()
                
                if coords:
                    result["location"] = {
                        "latitude": float(coords.latitude),
                        "longitude": float(coords.longitude),
                        "accuracy": submission.location_accuracy,
                        "altitude": submission.altitude
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get submission {submission_id}: {e}")
            import traceback
            logger.error(f"Get submission traceback: {traceback.format_exc()}")
            raise

    async def sync_submissions(self, sync_request: Dict[str, Any]) -> Dict[str, Any]:
        """Sync submissions with Kobo - basic implementation for now"""
        try:
            return {
                "operation_id": str(uuid.uuid4()),
                "status": "completed",
                "message": "Sync completed",
                "submissions_processed": 0,
                "submissions_synced": 0,
                "submissions_failed": 0,
                "started_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to sync submissions: {e}")
            import traceback
            logger.error(f"Sync submissions traceback: {traceback.format_exc()}")
            raise

    async def get_submission_stats(self) -> Dict[str, int]:
        """Get submission statistics"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=7)
            
            stats = {
                "total_submissions": self.db.query(FormSubmission).count(),
                "pending_sync": self.db.query(FormSubmission).filter(
                    FormSubmission.sync_status == "pending"
                ).count(),
                "synced": self.db.query(FormSubmission).filter(
                    FormSubmission.sync_status == "synced"
                ).count(),
                "failed_sync": self.db.query(FormSubmission).filter(
                    FormSubmission.sync_status == "failed"
                ).count(),
                "today_submissions": self.db.query(FormSubmission).filter(
                    FormSubmission.created_at >= today_start
                ).count(),
                "this_week_submissions": self.db.query(FormSubmission).filter(
                    FormSubmission.created_at >= week_start
                ).count(),
                "forms_with_submissions": self.db.query(FormTemplate.id).join(
                    FormSubmission
                ).distinct().count()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get submission stats: {e}")
            import traceback
            logger.error(f"Get submission stats traceback: {traceback.format_exc()}")
            raise

    async def delete_submission(self, submission_id: uuid.UUID) -> bool:
        """Delete a form submission"""
        try:
            submission = self.db.query(FormSubmission).filter(
                FormSubmission.id == submission_id
            ).first()
            
            if not submission:
                return False
            
            # Delete media files first
            media_files = self.db.query(MediaFile).filter(
                MediaFile.submission_id == submission_id
            ).all()
            
            for media_file in media_files:
                if media_file.file_path and os.path.exists(media_file.file_path):
                    try:
                        os.remove(media_file.file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete media file {media_file.file_path}: {e}")
                self.db.delete(media_file)
            
            # Delete submission
            self.db.delete(submission)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete submission {submission_id}: {e}")
            import traceback
            logger.error(f"Delete submission traceback: {traceback.format_exc()}")
            raise

    async def get_media_file(self, submission_id: uuid.UUID, media_id: uuid.UUID):
        """Get media file for download"""
        try:
            media_file = self.db.query(MediaFile).filter(
                and_(
                    MediaFile.id == media_id,
                    MediaFile.submission_id == submission_id
                )
            ).first()
            
            if not media_file:
                return None
            
            if not media_file.file_path or not os.path.exists(media_file.file_path):
                return None
            
            # Return file info (actual file serving would need FileResponse)
            return {
                "filename": media_file.original_filename,
                "mime_type": media_file.mime_type,
                "file_path": media_file.file_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get media file {media_id}: {e}")
            import traceback
            logger.error(f"Get media file traceback: {traceback.format_exc()}")
            raise

    async def resync_single_submission(self, submission_id: uuid.UUID) -> bool:
        """Resync a single submission"""
        try:
            submission = self.db.query(FormSubmission).filter(
                FormSubmission.id == submission_id
            ).first()
            
            if not submission:
                return False
            
            # Mark for resync
            submission.sync_status = "pending"
            submission.sync_attempts = 0
            submission.sync_error = None
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to resync submission {submission_id}: {e}")
            import traceback
            logger.error(f"Resync submission traceback: {traceback.format_exc()}")
            raise

    # Helper methods
    async def _get_or_create_form_template(self, kobo_form_id: str) -> FormTemplate:
        """Get existing form template or create from Kobo"""
        try:
            template = self.db.query(FormTemplate).filter(
                FormTemplate.kobo_form_id == kobo_form_id
            ).first()
            
            if template and template.is_active:
                return template
            
            # Create basic template (in real app, fetch from Kobo)
            if not template:
                template = FormTemplate(
                    kobo_form_id=kobo_form_id,
                    title=f"Form {kobo_form_id}",
                    description="Auto-created form template",
                    form_structure={"type": "basic_form"},
                    version="1.0"
                )
                self.db.add(template)
                self.db.commit()
                self.db.refresh(template)
            
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to get/create form template {kobo_form_id}: {e}")
            import traceback
            logger.error(f"Form template traceback: {traceback.format_exc()}")
            raise

    async def _get_or_create_user(self, username: str) -> User:
        """Get existing user or create new one"""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            
            if not user:
                user = User(username=username)
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to get/create user {username}: {e}")
            import traceback
            logger.error(f"User creation traceback: {traceback.format_exc()}")
            raise

    async def _save_media_files(self, submission_id: uuid.UUID, media_files: List[MediaFileUpload]):
        """Save media files to storage"""
        try:
            for media_data in media_files:
                try:
                    # Generate unique filename
                    file_extension = os.path.splitext(media_data.filename)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    file_path = os.path.join(self.media_storage_path, unique_filename)
                    
                    # Decode and save file
                    file_data = base64.b64decode(media_data.file_data)
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Create database record
                    media_file = MediaFile(
                        submission_id=submission_id,
                        filename=unique_filename,
                        original_filename=media_data.filename,
                        file_type=media_data.file_type,
                        mime_type=media_data.mime_type,
                        file_size=media_data.file_size,
                        file_path=file_path,
                        question_name=media_data.question_name,
                        upload_status="uploaded"
                    )
                    
                    self.db.add(media_file)
                    
                except Exception as e:
                    logger.error(f"Failed to save media file {media_data.filename}: {e}")
                    # Create failed record
                    media_file = MediaFile(
                        submission_id=submission_id,
                        filename=media_data.filename,
                        original_filename=media_data.filename,
                        file_type=media_data.file_type,
                        mime_type=media_data.mime_type,
                        file_size=media_data.file_size,
                        question_name=media_data.question_name,
                        upload_status="failed"
                    )
                    self.db.add(media_file)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save media files: {e}")
            import traceback
            logger.error(f"Save media files traceback: {traceback.format_exc()}")
            raise

    def _to_response_dict(self, submission: FormSubmission) -> Dict[str, Any]:
        """Convert database model to response dictionary"""
        try:
            result = {
                "id": submission.id,
                "kobo_form_id": submission.form_template.kobo_form_id,
                "status": submission.sync_status,
                "created_at": submission.created_at.isoformat(),
                "submitted_at": submission.submitted_at.isoformat(),
                "username": submission.user.username if submission.user else None,
                "device_id": submission.device_id
            }
            
            # Fix the location handling
            if submission.location:
                # Use PostGIS functions to extract coordinates
                from sqlalchemy import func
                coords = self.db.query(
                    func.ST_X(submission.location).label('longitude'),
                    func.ST_Y(submission.location).label('latitude')
                ).first()
                
                if coords:
                    result["location"] = {
                        "latitude": float(coords.latitude),
                        "longitude": float(coords.longitude),
                        "accuracy": submission.location_accuracy
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to convert submission to response dict: {e}")
            import traceback
            logger.error(f"Response dict traceback: {traceback.format_exc()}")
            raise

    def _media_file_to_dict(self, media_file: MediaFile) -> Dict[str, Any]:
        """Convert media file to response format"""
        try:
            return {
                "id": media_file.id,
                "filename": media_file.filename,
                "file_type": media_file.file_type,
                "mime_type": media_file.mime_type,
                "file_size": media_file.file_size,
                "question_name": media_file.question_name,
                "upload_status": media_file.upload_status,
                "created_at": media_file.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to convert media file to dict: {e}")
            import traceback
            logger.error(f"Media file dict traceback: {traceback.format_exc()}")
            raise