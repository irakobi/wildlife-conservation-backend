"""Forms management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from app.services.kobo_service import get_kobo_service, KoboService

router = APIRouter()

@router.get("/")
async def get_forms(kobo_service: KoboService = Depends(get_kobo_service)):
    """Get all forms from Kobo"""
    try:
        forms = await kobo_service.get_forms()
        parsed_forms = []
        
        for form in forms:
            parsed_form = await kobo_service.get_parsed_form(form['uid'])
            if parsed_form:
                parsed_forms.append(parsed_form)
        
        return {"forms": parsed_forms, "count": len(parsed_forms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{form_id}")
async def get_form(form_id: str, kobo_service: KoboService = Depends(get_kobo_service)):
    """Get specific form by ID"""
    try:
        parsed_form = await kobo_service.get_parsed_form(form_id)
        if not parsed_form:
            raise HTTPException(status_code=404, detail="Form not found")
        return parsed_form
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
