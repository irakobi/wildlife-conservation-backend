"""Main API router"""
from fastapi import APIRouter
from app.api.v1 import health, forms
# from app.api.v1 import health, forms, submissions

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(forms.router, prefix="/forms", tags=["Forms"])
# api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])