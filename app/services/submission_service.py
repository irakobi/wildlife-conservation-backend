# """
# Wildlife Submission Service
# Handles saving and managing wildlife conservation submissions to database
# """

# from typing import List, Optional, Dict, Any
# from sqlalchemy.orm import Session
# from sqlalchemy import and_, or_, text, func
# from datetime import datetime, timezone
# import uuid
# import json
# import logging
# from geoalchemy2 import Geography
# from geoalchemy2.functions import ST_Point, ST_DWithin

# from app.models.wildlife_models import (
#     WildlifeSubmission, FormTemplate, User, MediaFile, 
#     Species, SyncStatus, SubmissionStatus
# )
# from app.core.exceptions import ValidationException, DatabaseException
# from app.utils.kobo_parser import KoboFormParser

# logger = logging.getLogger(__name__)


# class SubmissionService:
#     """Service for managing wildlife submissions"""
    
#     def __init__(self, db: Session):
#         self.db = db
#         self.parser = KoboFormParser()
    
#     async def create_submission(
#         self, 
#         form_id: str, 
#         data: Dict[str, Any],
#         user_id: Optional[str] = None,
#         submitted_by: Optional[str] = None,
#         submission_source: str = "mobile"
#     ) -> WildlifeSubmission:
#         """Create a new wildlife submission"""
#         try:
#             # Get or create form template
#             form_template = await self._get_or_create_form_template(form_id)
            
#             # Parse and validate submission data
#             parsed_data = self._parse_submission_data(data, form_template)
            
#             # Extract location data
#             location_point = self._extract_location(parsed_data)
            
#             # Create submission record
#             submission = WildlifeSubmission(
#                 id=uuid.uuid4(),
#                 form_template_id=form_template.id,
#                 kobo_form_uid=form_id,
#                 user_id=uuid.UUID(user_id) if user_id else None,
                
#                 # Incident details from parsed data
#                 incident_date=self._parse_date(parsed_data.get('incident_date')),
#                 incident_time=parsed_data.get('incident_time'),
#                 location=location_point,
#                 location_accuracy=parsed_data.get('location_accuracy'),
#                 location_name=parsed_data.get('location_name'),
#                 administrative_area=parsed_data.get('administrative_area', {}),
                
#                 # Wildlife information
#                 species=parsed_data.get('species'),
#                 species_count=self._parse_int(parsed_data.get('species_count'), 1),
#                 species_behavior=parsed_data.get('species_behavior'),
                
#                 # Incident classification
#                 incident_type=parsed_data.get('incident_type', 'other'),
#                 incident_severity=parsed_data.get('incident_severity', 'medium'),
#                 conflict_type=parsed_data.get('conflict_type', []),
                
#                 # Description
#                 description=parsed_data.get('description'),
#                 circumstances=parsed_data.get('circumstances'),
#                 immediate_response=parsed_data.get('immediate_response'),
                
#                 # Reporter information
#                 reporter_name=submitted_by or parsed_data.get('reporter_name'),
#                 reporter_contact=parsed_data.get('reporter_contact'),
#                 reporter_type=parsed_data.get('reporter_type', 'community_member'),
                
#                 # Impact assessment
#                 crop_damage_area=self._parse_float(parsed_data.get('crop_damage_area')),
#                 livestock_lost=self._parse_int(parsed_data.get('livestock_lost')),
#                 property_damage_value=self._parse_float(parsed_data.get('property_damage_value')),
#                 human_casualties=self._parse_int(parsed_data.get('human_casualties')),
                
#                 # Workflow
#                 status=SubmissionStatus.SUBMITTED,
#                 priority=self._parse_int(parsed_data.get('priority'), 3),
                
#                 # Sync status
#                 sync_status=SyncStatus.PENDING,
#                 sync_attempts=0,
                
#                 # Raw data
#                 raw_form_data=data,
#                 processed_data=parsed_data,
                
#                 # Metadata
#                 submission_source=submission_source,
#                 device_info=parsed_data.get('device_info', {}),
#                 submitted_at=datetime.now(timezone.utc)
#             )
            
#             # Save to database
#             self.db.add(submission)
#             self.db.commit()
#             self.db.refresh(submission)
            
#             # Handle media files if present
#             await self._process_media_files(submission, parsed_data)
            
#             logger.info(f"Created submission: {submission.id}")
#             return submission
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Failed to create submission: {e}")
#             raise DatabaseException(f"Failed to create submission: {str(e)}")
    
#     async def get_submissions(
#         self, 
#         form_id: Optional[str] = None,
#         user_id: Optional[str] = None,
#         status: Optional[str] = None,
#         species: Optional[str] = None,
#         location_filter: Optional[Dict] = None,
#         date_from: Optional[datetime] = None,
#         date_to: Optional[datetime] = None,
#         limit: int = 50,
#         offset: int = 0
#     ) -> List[WildlifeSubmission]:
#         """Get submissions with filtering"""
#         try:
#             query = self.db.query(WildlifeSubmission)
            
#             # Apply filters
#             if form_id:
#                 query = query.filter(WildlifeSubmission.kobo_form_uid == form_id)
            
#             if user_id:
#                 query = query.filter(WildlifeSubmission.user_id == uuid.UUID(user_id))
            
#             if status:
#                 query = query.filter(WildlifeSubmission.status == status)
            
#             if species:
#                 query = query.filter(WildlifeSubmission.species == species)
            
#             if date_from:
#                 query = query.filter(WildlifeSubmission.incident_date >= date_from)
            
#             if date_to:
#                 query = query.filter(WildlifeSubmission.incident_date <= date_to)
            
#             # Location filter (within radius of point)
#             if location_filter and 'lat' in location_filter and 'lng' in location_filter:
#                 point = ST_Point(location_filter['lng'], location_filter['lat'])
#                 radius = location_filter.get('radius_meters', 10000)  # Default 10km
#                 query = query.filter(
#                     ST_DWithin(WildlifeSubmission.location, point, radius)
#                 )
            
#             # Order by most recent first
#             query = query.order_by(WildlifeSubmission.submitted_at.desc())
            
#             # Apply pagination
#             submissions = query.offset(offset).limit(limit).all()
            
#             return submissions
            
#         except Exception as e:
#             logger.error(f"Failed to get submissions: {e}")
#             raise DatabaseException(f"Failed to retrieve submissions: {str(e)}")
    
#     async def get_submission_by_id(self, submission_id: str) -> Optional[WildlifeSubmission]:
#         """Get specific submission by ID"""
#         try:
#             submission = self.db.query(WildlifeSubmission).filter(
#                 WildlifeSubmission.id == uuid.UUID(submission_id)
#             ).first()
            
#             return submission
            
#         except Exception as e:
#             logger.error(f"Failed to get submission {submission_id}: {e}")
#             raise DatabaseException(f"Failed to retrieve submission: {str(e)}")
    
#     async def update_submission(
#         self, 
#         submission_id: str, 
#         updates: Dict[str, Any]
#     ) -> Optional[WildlifeSubmission]:
#         """Update an existing submission"""
#         try:
#             submission = await self.get_submission_by_id(submission_id)
#             if not submission:
#                 return None
            
#             # Update allowed fields
#             allowed_fields = [
#                 'status', 'priority', 'assigned_to', 'response_actions',
#                 'resolution_details', 'follow_up_required', 'follow_up_date',
#                 'is_verified', 'verification_notes'
#             ]
            
#             for field, value in updates.items():
#                 if field in allowed_fields and hasattr(submission, field):
#                     setattr(submission, field, value)
            
#             submission.updated_at = datetime.now(timezone.utc)
            
#             self.db.commit()
#             self.db.refresh(submission)
            
#             return submission
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Failed to update submission {submission_id}: {e}")
#             raise DatabaseException(f"Failed to update submission: {str(e)}")
    
#     async def mark_synced(self, submission_id: str, kobo_submission_id: Optional[str] = None):
#         """Mark submission as successfully synced to Kobo"""
#         try:
#             submission = await self.get_submission_by_id(submission_id)
#             if submission:
#                 submission.sync_status = SyncStatus.SYNCED
#                 submission.kobo_submission_id = kobo_submission_id
#                 submission.last_sync_attempt = datetime.now(timezone.utc)
                
#                 self.db.commit()
                
#         except Exception as e:
#             logger.error(f"Failed to mark submission as synced: {e}")
    
#     async def mark_sync_failed(self, submission_id: str, error_message: str):
#         """Mark submission sync as failed"""
#         try:
#             submission = await self.get_submission_by_id(submission_id)
#             if submission:
#                 submission.sync_status = SyncStatus.FAILED
#                 submission.sync_attempts += 1
#                 submission.sync_error = error_message
#                 submission.last_sync_attempt = datetime.now(timezone.utc)
                
#                 self.db.commit()
                
#         except Exception as e:
#             logger.error(f"Failed to mark submission sync as failed: {e}")
    
#     async def get_pending_syncs(self, limit: int = 10) -> List[WildlifeSubmission]:
#         """Get submissions pending sync to Kobo"""
#         try:
#             submissions = self.db.query(WildlifeSubmission).filter(
#                 and_(
#                     WildlifeSubmission.sync_status.in_([SyncStatus.PENDING, SyncStatus.RETRY]),
#                     WildlifeSubmission.sync_attempts < 3
#                 )
#             ).limit(limit).all()
            
#             return submissions
            
#         except Exception as e:
#             logger.error(f"Failed to get pending syncs: {e}")
#             return []
    
#     def _parse_submission_data(
#         self, 
#         data: Dict[str, Any], 
#         form_template: FormTemplate
#     ) -> Dict[str, Any]:
#         """Parse and clean submission data"""
#         try:
#             if form_template.structure:
#                 # Use form structure to parse data
#                 return self.parser.parse_submission_data(data, form_template.structure)
#             else:
#                 # Basic parsing without form structure
#                 return data
                
#         except Exception as e:
#             logger.warning(f"Data parsing failed, using raw data: {e}")
#             return data
    
#     def _extract_location(self, data: Dict[str, Any]) -> Optional[str]:
#         """Extract and format location data"""
#         try:
#             location = data.get('location')
#             if not location:
#                 return None
            
#             if isinstance(location, str):
#                 # Parse "lat,lng" format
#                 coords = location.split(',')
#                 if len(coords) >= 2:
#                     lat, lng = float(coords[0].strip()), float(coords[1].strip())
#                     return f"POINT({lng} {lat})"  # PostGIS format: lng lat
            
#             elif isinstance(location, dict):
#                 # Parse coordinate object
#                 lat = location.get('latitude') or location.get('lat')
#                 lng = location.get('longitude') or location.get('lng')
#                 if lat and lng:
#                     return f"POINT({lng} {lat})"
            
#             return None
            
#         except Exception as e:
#             logger.warning(f"Failed to parse location: {e}")
#             return None
    
#     def _parse_date(self, date_value: Any) -> Optional[datetime]:
#         """Parse date from various formats"""
#         if not date_value:
#             return None
        
#         try:
#             if isinstance(date_value, datetime):
#                 return date_value
            
#             if isinstance(date_value, str):
#                 # Try common date formats
#                 from dateutil import parser
#                 return parser.parse(date_value)
            
#             return None
            
#         except Exception as e:
#             logger.warning(f"Failed to parse date '{date_value}': {e}")
#             return None
    
#     def _parse_int(self, value: Any, default: int = 0) -> int:
#         """Safely parse integer value"""
#         try:
#             if value is None:
#                 return default
#             return int(value)
#         except (ValueError, TypeError):
#             return default
    
#     def _parse_float(self, value: Any, default: float = 0.0) -> float:
#         """Safely parse float value"""
#         try:
#             if value is None:
#                 return default
#             return float(value)
#         except (ValueError, TypeError):
#             return default
    
#     async def _get_or_create_form_template(self, form_id: str) -> FormTemplate:
#         """Get existing form template or create a new one"""
#         try:
#             form_template = self.db.query(FormTemplate).filter(
#                 FormTemplate.kobo_uid == form_id
#             ).first()
            
#             if not form_template:
#                 # Create new form template
#                 form_template = FormTemplate(
#                     kobo_uid=form_id,
#                     name=f"Form {form_id}",
#                     title="Wildlife Survey Form",
#                     is_active=True
#                 )
#                 self.db.add(form_template)
#                 self.db.commit()
#                 self.db.refresh(form_template)
                
#                 logger.info(f"Created new form template: {form_id}")
            
#             return form_template
            
#         except Exception as e:
#             logger.error(f"Failed to get/create form template: {e}")
#             raise DatabaseException(f"Form template error: {str(e)}")
    
#     async def _process_media_files(
#         self, 
#         submission: WildlifeSubmission, 
#         data: Dict[str, Any]
#     ):
#         """Process and save media files associated with submission"""
#         try:
#             media_fields = ['photos', 'videos', 'audio_notes', 'documents']
            
#             for field in media_fields:
#                 if field in data and data[field]:
#                     await self._save_media_files(submission, field, data[field])
                    
#         except Exception as e:
#             logger.error(f"Failed to process media files: {e}")
    
#     async def _save_media_files(
#         self, 
#         submission: WildlifeSubmission, 
#         field_type: str, 
#         files: List[Dict]
#     ):
#         """Save individual media files"""
#         # This is a placeholder - implement actual file handling
#         # based on your storage solution (local, S3, etc.)
#         pass
    
#     async def get_submission_statistics(
#         self, 
#         date_from: Optional[datetime] = None,
#         date_to: Optional[datetime] = None
#     ) -> Dict[str, Any]:
#         """Get statistics about submissions"""
#         try:
#             query = self.db.query(WildlifeSubmission)
            
#             if date_from:
#                 query = query.filter(WildlifeSubmission.submitted_at >= date_from)
#             if date_to:
#                 query = query.filter(WildlifeSubmission.submitted_at <= date_to)
            
#             total_count = query.count()
            
#             # Count by status
#             status_counts = {}
#             for status in SubmissionStatus:
#                 count = query.filter(WildlifeSubmission.status == status).count()
#                 status_counts[status.value] = count
            
#             # Count by species
#             species_query = self.db.query(
#                 WildlifeSubmission.species,
#                 func.count(WildlifeSubmission.id).label('count')
#             ).filter(WildlifeSubmission.species.isnot(None))
            
#             if date_from:
#                 species_query = species_query.filter(WildlifeSubmission.submitted_at >= date_from)
#             if date_to:
#                 species_query = species_query.filter(WildlifeSubmission.submitted_at <= date_to)
            
#             species_counts = {
#                 species: count for species, count in 
#                 species_query.group_by(WildlifeSubmission.species).all()
#             }
            
#             # Count by incident type
#             type_query = self.db.query(
#                 WildlifeSubmission.incident_type,
#                 func.count(WildlifeSubmission.id).label('count')
#             )
            
#             if date_from:
#                 type_query = type_query.filter(WildlifeSubmission.submitted_at >= date_from)
#             if date_to:
#                 type_query = type_query.filter(WildlifeSubmission.submitted_at <= date_to)
            
#             type_counts = {
#                 incident_type: count for incident_type, count in 
#                 type_query.group_by(WildlifeSubmission.incident_type).all()
#             }
            
#             return {
#                 "total_submissions": total_count,
#                 "status_breakdown": status_counts,
#                 "species_breakdown": species_counts,
#                 "incident_type_breakdown": type_counts,
#                 "period": {
#                     "from": date_from.isoformat() if date_from else None,
#                     "to": date_to.isoformat() if date_to else None
#                 }
#             }
            
#         except Exception as e:
#             logger.error(f"Failed to get statistics: {e}")
#             raise DatabaseException(f"Failed to get statistics: {str(e)}")