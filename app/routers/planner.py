# app/routers/planner.py

from fastapi import APIRouter, HTTPException
from .. import schemas, service

router = APIRouter(
    prefix="/planner",
    tags=["Planner"]
)

@router.post("/generate-plans", response_model=schemas.PlannerResponse)
async def generate_comprehensive_plans(request: schemas.MobilityRequest):
    try:
        full_plan = await service.MasterPlannerAgent.generate_plans(request)
        return full_plan
    except Exception as e:
        # エラーログを出すとデバッグに役立ちます
        print(f"Error in planner endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plans.")