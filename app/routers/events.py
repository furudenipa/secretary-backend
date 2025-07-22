# app/routers/events.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from .. import crud, schemas, models, user_profile
from ..database import get_db

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

@router.post("/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_new_event(
    event: schemas.EventCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    if event.start_time >= event.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time."
        )
    created_event = await crud.create_event(db=db, event=event)

    # 予定の変更をトリガーに、必要であればプロフィールをバックグラウンドで再生成
    background_tasks.add_task(
        user_profile.UserProfileService.regenerate_profile_if_stale, db=db
    )
    return created_event

@router.get("/", response_model=List[schemas.Event])
async def read_events(start: datetime, end: datetime, db: AsyncSession = Depends(get_db)):
    return await crud.get_events_by_period(db, start=start, end=end)

@router.get("/{event_id}", response_model=schemas.Event)
async def read_event(event_id: int, db: AsyncSession = Depends(get_db)):
    db_event = await crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return db_event

@router.put("/{event_id}", response_model=schemas.Event)
async def update_existing_event(
    event_id: int,
    event: schemas.EventUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    db_event = await crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    updated_event = await crud.update_event(db=db, db_event=db_event, event_update=event)

    # 予定の変更をトリガーに、必要であればプロフィールをバックグラウンドで再生成
    background_tasks.add_task(
        user_profile.UserProfileService.regenerate_profile_if_stale, db=db
    )
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_event(event_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_event = await crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await crud.delete_event(db=db, db_event=db_event)
    # 予定の変更をトリガーに、必要であればプロフィールをバックグラウンドで再生成
    background_tasks.add_task(
        user_profile.UserProfileService.regenerate_profile_if_stale, db=db
    )
    return

@router.get("/recently-updated/", response_model=List[schemas.Event])
async def read_recently_updated_events(
    limit: int = Query(5, ge=1, le=100, description="取得する最大件数"),
    db: AsyncSession = Depends(get_db),
):
    """
    最近追加された予定を取得します。

    - **limit**: 取得する件数を指定します (デフォルト: 5, 最小: 1, 最大: 100)。
    """
    events = await crud.get_recently_updated_events(db=db, limit=limit)
    return events
