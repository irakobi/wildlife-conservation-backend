"""
Kobo Toolbox API Integration Service
Handles all interactions with Kobo Toolbox API
"""

import logging
from typing import Dict, List, Optional, Any
import httpx
import asyncio
from datetime import datetime, timezone
import json
from urllib.parse import urljoin

from app.config import settings, get_kobo_config
from app.utils.kobo_parser import KoboFormParser
from app.core.exceptions import KoboAPIException

logger = logging.getLogger(__name__)


class KoboService:
    """Service for interacting with Kobo Toolbox API"""
    
    def __init__(self):
        self.config = get_kobo_config()
        self.api_token = self.config["api_token"]
        self.server_url = self.config["server_url"].rstrip('/')
        self.timeout = self.config["timeout"]
        self.parser = KoboFormParser()
        
        # HTTP client configuration
        self.headers = {
            'Authorization': f'Token {self.api_token}',
            # 'Content-Type': 'application/json',
            'User-Agent': f'WildlifeConservationAPI/{settings.app_version}',
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Kobo API with error handling"""
        url = urljoin(self.server_url + '/', endpoint.lstrip('/'))
        
        try:
            # Copy headers to modify per request
            headers = self.headers.copy()

            # Force JSON response for GET/DELETE requests
            if method.upper() in ["GET", "DELETE"]:
                headers["Accept"] = "application/json"

            # Ensure POST/PUT/PATCH requests send JSON
            if method.upper() in ["POST", "PUT", "PATCH"]:
                headers["Content-Type"] = "application/json"
                headers["Accept"] = "application/json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Kobo API {method.upper()}: {url}")

                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                # Log response details
                logger.debug(f"Kobo API Response: {response.status_code}")
                
                # Handle different response status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 201:
                    return response.json()
                elif response.status_code == 204:
                    return {"success": True}
                elif response.status_code == 401:
                    raise KoboAPIException(
                        "Authentication failed. Check your Kobo API token.",
                        status_code=401
                    )
                elif response.status_code == 403:
                    raise KoboAPIException(
                        "Access denied. Insufficient permissions.",
                        status_code=403
                    )
                elif response.status_code == 404:
                    raise KoboAPIException(
                        f"Resource not found: {endpoint}",
                        status_code=404
                    )
                elif response.status_code == 429:
                    raise KoboAPIException(
                        "Rate limit exceeded. Please try again later.",
                        status_code=429
                    )
                else:
                    error_text = response.text
                    raise KoboAPIException(
                        f"Kobo API error: {response.status_code} - {error_text}",
                        status_code=response.status_code
                    )
                    
        except httpx.TimeoutException:
            raise KoboAPIException(
                f"Request timeout after {self.timeout}s",
                status_code=408
            )
        except httpx.RequestError as e:
            raise KoboAPIException(
                f"Request error: {str(e)}",
                status_code=500
            )
        except Exception as e:
            logger.error(f"Unexpected error in Kobo API request: {e}")
            raise KoboAPIException(
                f"Unexpected error: {str(e)}",
                status_code=500
            )
    
    async def test_connection(self) -> bool:
        """Test connection to Kobo API"""
        try:
            await self._make_request("GET", "/api/v2/assets/", params={"limit": 1})
            logger.info("✅ Kobo API connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Kobo API connection failed: {e}")
            return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        try:
            user_data = await self._make_request("GET", "/api/v2/me/")
            return {
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "is_superuser": user_data.get("is_superuser", False),
                "date_joined": user_data.get("date_joined"),
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    async def get_forms(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all forms (assets) from Kobo account"""
        try:
            params = {
                "limit": limit,
                "offset": offset,
                "asset_type": "survey"  # Only get survey forms
            }
            
            response = await self._make_request("GET", "/api/v2/assets/", params=params)
            forms = response.get("results", [])
            
            logger.info(f"Retrieved {len(forms)} forms from Kobo")
            return forms
            
        except Exception as e:
            logger.error(f"Failed to get forms: {e}")
            raise
    
    async def get_form_by_uid(self, form_uid: str) -> Optional[Dict[str, Any]]:
        """Get specific form by UID"""
        try:
            form_data = await self._make_request("GET", f"/api/v2/assets/{form_uid}/")
            logger.info(f"Retrieved form: {form_data.get('name', form_uid)}")
            return form_data
        except KoboAPIException as e:
            if e.status_code == 404:
                logger.warning(f"Form not found: {form_uid}")
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get form {form_uid}: {e}")
            raise
    
    async def get_parsed_form(self, form_uid: str) -> Optional[Dict[str, Any]]:
        """Get form and parse it for mobile app consumption"""
        try:
            form_data = await self.get_form_by_uid(form_uid)
            if not form_data:
                return None
            
            parsed_form = self.parser.parse_form_content(form_data)
            return parsed_form
        except Exception as e:
            logger.error(f"Failed to parse form {form_uid}: {e}")
            raise
    
    async def get_form_submissions(
        self, 
        form_uid: str, 
        limit: int = 100, 
        start: int = 0,
        sort: str = "-_submission_time"
    ) -> Dict[str, Any]:
        """Get submissions for a specific form"""
        try:
            params = {
                "limit": limit,
                "start": start,
                "sort": sort,
                "format": "json"
            }
            
            response = await self._make_request(
                "GET", 
                f"/api/v2/assets/{form_uid}/data/", 
                params=params
            )
            
            submissions = response.get("results", [])
            logger.info(f"Retrieved {len(submissions)} submissions for form {form_uid}")
            
            return {
                "results": submissions,
                "count": response.get("count", len(submissions)),
                "next": response.get("next"),
                "previous": response.get("previous")
            }
            
        except Exception as e:
            logger.error(f"Failed to get submissions for form {form_uid}: {e}")
            raise
    
    async def submit_data(
        self, 
        form_uid: str, 
        submission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit data to a Kobo form"""
        try:
            # Prepare submission data in Kobo format
            kobo_submission = {
                "submission": submission_data,
                "meta/instanceID": f"uuid:{submission_data.get('_uuid', '')}",
                "meta/submissionTime": datetime.now(timezone.utc).isoformat(),
            }
            
            response = await self._make_request(
                "POST",
                f"/api/v2/assets/{form_uid}/submissions/",
                data=kobo_submission
            )
            
            logger.info(f"Successfully submitted data to form {form_uid}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to submit data to form {form_uid}: {e}")
            raise
    
    async def update_submission(
        self, 
        form_uid: str, 
        submission_id: str, 
        submission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing submission"""
        try:
            response = await self._make_request(
                "PUT",
                f"/api/v2/assets/{form_uid}/submissions/{submission_id}/",
                data=submission_data
            )
            
            logger.info(f"Successfully updated submission {submission_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to update submission {submission_id}: {e}")
            raise
    
    async def delete_submission(
        self, 
        form_uid: str, 
        submission_id: str
    ) -> bool:
        """Delete a submission"""
        try:
            await self._make_request(
                "DELETE",
                f"/api/v2/assets/{form_uid}/submissions/{submission_id}/"
            )
            
            logger.info(f"Successfully deleted submission {submission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete submission {submission_id}: {e}")
            raise
    
    async def get_form_schema(self, form_uid: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a form"""
        try:
            form_data = await self.get_form_by_uid(form_uid)
            if not form_data:
                return None
            
            content = form_data.get("content", {})
            return {
                "survey": content.get("survey", []),
                "choices": content.get("choices", []),
                "settings": content.get("settings", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get form schema {form_uid}: {e}")
            raise
    
    async def search_forms(self, query: str) -> List[Dict[str, Any]]:
        """Search forms by name or description"""
        try:
            params = {
                "q": query,
                "asset_type": "survey"
            }
            
            response = await self._make_request("GET", "/api/v2/assets/", params=params)
            forms = response.get("results", [])
            
            logger.info(f"Found {len(forms)} forms matching '{query}'")
            return forms
            
        except Exception as e:
            logger.error(f"Failed to search forms: {e}")
            raise
    
    async def get_api_usage(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            # This endpoint might not exist in all Kobo instances
            # It's more of a placeholder for potential usage tracking
            response = await self._make_request("GET", "/api/v2/me/")
            
            return {
                "requests_today": response.get("api_requests_today", 0),
                "requests_this_month": response.get("api_requests_month", 0),
                "rate_limit_remaining": response.get("rate_limit_remaining", "unknown"),
            }
            
        except Exception:
            # Return default values if endpoint doesn't exist
            return {
                "requests_today": "unknown",
                "requests_this_month": "unknown", 
                "rate_limit_remaining": "unknown",
            }
    
    async def bulk_submit_data(
        self, 
        form_uid: str, 
        submissions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Submit multiple submissions to a form"""
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, submission_data in enumerate(submissions):
            try:
                await self.submit_data(form_uid, submission_data)
                results["successful"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "data": submission_data,
                    "error": str(e)
                })
                logger.error(f"Failed to submit bulk data item {i}: {e}")
        
        logger.info(
            f"Bulk submission completed: {results['successful']} successful, "
            f"{results['failed']} failed"
        )
        
        return results


# Global KoboService instance
kobo_service = KoboService()


async def get_kobo_service() -> KoboService:
    """Dependency function to get Kobo service"""
    return kobo_service


# Health check function for Kobo API
async def check_kobo_health() -> Dict[str, Any]:
    """Check Kobo API health status"""
    try:
        is_connected = await kobo_service.test_connection()
        user_info = await kobo_service.get_user_info() if is_connected else None
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "server_url": settings.kobo_server_url,
            "user": user_info.get("username") if user_info else None,
            "last_checked": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "server_url": settings.kobo_server_url,
            "last_checked": datetime.now(timezone.utc).isoformat()
        }