# app/crud.py

from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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