# app/routers/suggestions.py

from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, services

router = APIRouter(
    prefix="/suggestions",
    tags=["Suggestions"]
)

@router.post("/", response_model=schemas.SuggestionResponse)
async def get_suggestions_for_free_time(request_body: schemas.SuggestionRequest):
    try:
        suggestions = await services.GoogleSearchService.search_suggestions(request_body)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        # 外部APIのエラーなどを捕捉
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch suggestions: {e}")