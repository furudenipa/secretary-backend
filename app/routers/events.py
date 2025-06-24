# app/routers/events.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from .. import crud, schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

@router.post("/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_new_event(event: schemas.EventCreate, db: AsyncSession = Depends(get_db)):
    if event.start_time >= event.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time."
        )
    return await crud.create_event(db=db, event=event)

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
async def update_existing_event(event_id: int, event: schemas.EventUpdate, db: AsyncSession = Depends(get_db)):
    db_event = await crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return await crud.update_event(db=db, db_event=db_event, event_update=event)

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_event(event_id: int, db: AsyncSession = Depends(get_db)):
    db_event = await crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await crud.delete_event(db=db, db_event=db_event)
    return