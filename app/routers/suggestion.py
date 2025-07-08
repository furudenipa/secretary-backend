# app/routers/suggestions.py

from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, service

router = APIRouter(
    prefix="/suggestions",
    tags=["Suggestions"]
)

@router.post("/", response_model=schemas.SuggestionResponse)
async def get_suggestions_for_free_time(request_body: schemas.SuggestionRequest):
    try:
        suggestions = await service.SuggestionService.get_suggestions(request_body)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConnectionError as e:
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")