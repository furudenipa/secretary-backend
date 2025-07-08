from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- Event Schemas ---

# 予定作成時のリクエストボディ
class EventCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None

# 予定更新時のリクエストボディ
class EventUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None

# DBから読み取ったデータをAPIレスポンス用に変換
class Event(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # ORMモデルをPydanticモデルに変換できるようにする

# --- Suggestion Schemas ---

# 提案機能で利用する直前・直後の予定情報
class AdjacentEventInfo(BaseModel):
    time: datetime
    content: Optional[str] = None
    location: Optional[str] = None

# 予定提案APIのリクエストボディ
class SuggestionRequest(BaseModel):
    free_time_start: datetime
    free_time_end: datetime
    prev_event: Optional[AdjacentEventInfo] = None
    next_event: Optional[AdjacentEventInfo] = None

# 提案結果のスキーマ
class Suggestion(BaseModel):
    title: str
    link: str
    snippet: str

# 予定提案APIのレスポンス
class SuggestionResponse(BaseModel):
    query: str
    suggestions: list[Suggestion]

# --- User Profile Schemas ---
class UserProfileResponse(BaseModel):
    food_preferences: str
    activity_preferences: str
    outing_tendency: str
