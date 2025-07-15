# app/crud.py

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from . import models, schemas
from datetime import datetime

# --- Event CRUD ---

async def get_event(db: AsyncSession, event_id: int) -> models.Event | None:
    result = await db.execute(select(models.Event).filter(models.Event.id == event_id))
    return result.scalars().first()

async def get_events_by_period(db: AsyncSession, start: datetime, end: datetime) -> Sequence[models.Event]:
    result = await db.execute(
        select(models.Event)
        .filter(models.Event.start_time < end, models.Event.end_time > start)
        .order_by(models.Event.start_time)
    )
    return result.scalars().all()

async def get_recently_updated_events(db: AsyncSession, limit: int = 5) -> Sequence[models.Event]:
    """最近追加された予定を取得する"""
    result = await db.execute(
        select(models.Event)
        .order_by(models.Event.updated_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def create_event(db: AsyncSession, event: schemas.EventCreate) -> models.Event:
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event

#
async def update_event(db: AsyncSession, db_event: models.Event, event_update: schemas.EventUpdate) -> models.Event:
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    await db.commit()
    await db.refresh(db_event)
    return db_event

#
async def delete_event(db: AsyncSession, db_event: models.Event) -> models.Event:
    await db.delete(db_event)
    await db.commit()
    return db_event


async def get_previous_event(db: AsyncSession, target_time: datetime) -> models.Event | None:
    """指定された時間と同じ日付で、それより前に終了する最も直近のイベントを取得する"""
    target_date = target_time.date()
    result = await db.execute(
        select(models.Event)
        .filter(
            func.date(models.Event.end_time) == target_date,
            models.Event.end_time <= target_time
        )
        .order_by(models.Event.end_time.desc())
        .limit(1)
    )
    return result.scalars().first()

async def get_next_event(db: AsyncSession, target_time: datetime) -> models.Event | None:
    """指定された時間と同じ日付で、それより後に開始する最も直近のイベントを取得する"""
    target_date = target_time.date()
    result = await db.execute(
        select(models.Event)
        .filter(
            func.date(models.Event.start_time) == target_date,
            models.Event.start_time >= target_time
        )
        .order_by(models.Event.start_time.asc())
        .limit(1)
    )
    return result.scalars().first()