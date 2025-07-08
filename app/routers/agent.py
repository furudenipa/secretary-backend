# app/routers/agent.py

from fastapi import APIRouter, HTTPException
from .. import schemas, service

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)

@router.post("/decide-mobility", response_model=schemas.MobilityResponse)
async def decide_user_mobility(request: schemas.MobilityRequest):
    try:
        decision = await service.MobilityAgent.decide_mobility(request)
        return decision
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")