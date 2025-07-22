# app/routers/masculine_planner.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, service, crud
from ..database import get_db


router = APIRouter(
    prefix="/masculine-planner",
    tags=["Masculine Planner"]
)

@router.post("/generate-plans", response_model=schemas.PlannerResponse)
async def generate_masculine_plans_from_free_time(
    request: schemas.ConveniencePlannerRequest,
    db: AsyncSession = Depends(get_db)
):
    """トライアスリート向けに、過酷なトレーニングプランを生成します。"""
    
    prev_event_db = await crud.get_previous_event(db, request.free_time_start)
    next_event_db = await crud.get_next_event(db, request.free_time_end)

    prev_event_end_time = prev_event_db.end_time if prev_event_db else request.free_time_start
    prev_event_location = prev_event_db.location if prev_event_db else "現在地"

    next_event_start_time = next_event_db.start_time if next_event_db else request.free_time_end
    next_event_location = next_event_db.location if next_event_db else "目的地"
    
    # JST = ZoneInfo("Asia/Tokyo")
    # if prev_event_end_time.tzinfo is None:
    #     prev_event_end_time = prev_event_end_time.replace(tzinfo=JST)
    # if next_event_start_time.tzinfo is None:
    #     next_event_start_time = next_event_start_time.replace(tzinfo=JST)

    # if prev_event_end_time >= next_event_start_time:
    #     raise HTTPException(status_code=400, detail="イベントの時間関係が不正です。")

    # MasculineAgentに渡すリクエストを作成
    agent_request = schemas.MobilityRequest(
        prev_event_end_time=prev_event_end_time,
        prev_event_location=prev_event_location,
        next_event_start_time=next_event_start_time,
        next_event_location=next_event_location,
        user_preferences=request.user_preferences
    )

    try:
        # MasculineAgentを呼び出す
        full_plan = await service.MasculineAgent.generate_plans(agent_request)
        return full_plan
    except Exception as e:
        print(f"Error in masculine planner endpoint: {e}")
        raise HTTPException(status_code=500, detail="プランの生成に失敗しました。")