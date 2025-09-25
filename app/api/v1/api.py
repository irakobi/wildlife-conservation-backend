# """Main API router"""
# from fastapi import APIRouter
# from app.api.v1 import health, forms, submissions


# api_router = APIRouter()

# api_router.include_router(health.router, prefix="/health", tags=["Health"])
# api_router.include_router(forms.router, prefix="/forms", tags=["Forms"])
# api_router.include_router(submissions.router, prefix="/submissions", tags=["Form Submissions"])

# app/api/v1/api.py
"""Main API router with all endpoints"""
from fastapi import APIRouter

# Import existing routers
from app.api.v1 import health, forms

# Import submissions router (this might be missing!)
try:
    from app.api.v1 import submissions
    SUBMISSIONS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import submissions router: {e}")
    SUBMISSIONS_AVAILABLE = False

# Create main API router
api_router = APIRouter()

# Include existing routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(forms.router, prefix="/forms", tags=["Forms"])

# Include submissions router if available
if SUBMISSIONS_AVAILABLE:
    api_router.include_router(submissions.router, prefix="/submissions", tags=["Form Submissions"])
    print("✅ Submissions router included successfully")
else:
    print("❌ Submissions router not included - check imports")