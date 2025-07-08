from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

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


# --- Suggestion Schemas (大幅に強化) ---

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

# 新機能：移動区間のためのスキーマ
class ItineraryLeg(BaseModel):
    mode: str  # 例: "徒歩", "電車", "タクシー"
    duration_minutes: int
    instructions: str # 例: "京都駅から烏丸線で四条駅まで"

# 新機能：提案内容本体のスキーマ
class Suggestion(BaseModel):
    title: str
    description: str
    activity_start_time: datetime
    activity_end_time: datetime
    location: Optional[str] = None
    estimated_cost: Optional[str] = "不明"
    # 前の予定からの移動プラン
    travel_from_previous: Optional[ItineraryLeg] = None
    # 次の予定への移動プラン
    travel_to_next: Optional[ItineraryLeg] = None
    source_link: Optional[str] = None # Tavilyの検索ソース

# 予定提案APIのレスポンス
class SuggestionResponse(BaseModel):
    search_query: str # Tavilyで検索したクエリ
    suggestions: List[Suggestion]

# 移動判別エージェントへのリクエスト
class MobilityRequest(BaseModel):
    prev_event_location: str # 前のイベントの場所
    next_event_location: str # 次のイベントの場所
    prev_event_end_time : datetime #前のイベントの終了時刻
    next_event_start_time: datetime # 次のイベントの開始時刻
    user_preferences: str # 例: 「時間はかかってもいいから安く済ませたい」「歩くのは好き」「とにかく早く着きたい」など

# 移動判別エージェントからのレスポンス
class MobilityResponse(BaseModel):
    use_public_transport: bool # 公共交通機関を使うべきか (True/False)
    recommended_mode: str      # 具体的な推奨移動手段 (例: "公共交通機関", "徒歩")
    reasoning: str             # なぜそのように判断したかの理由
    estimated_time: int        # 推定所要時間（分）
    estimated_cost: str        # 推定料金


# 1つの行動プランは、テーマと「イベントのリスト」で構成される
class PlanPattern(BaseModel):
    pattern_description: str        # 例: "静かなカフェで読書プラン"
    events: List[EventCreate]       # このプランを構成するイベントのシーケンス

# 最終的なプランナーからのレスポンス
class PlannerResponse(BaseModel):
    mobility_decision: MobilityResponse # 移動判断の結果
    plans: List[PlanPattern]            # 提案プランのリスト（2パターン）

# # --- Suggestion Schemas ---

# # 提案機能で利用する直前・直後の予定情報
# class AdjacentEventInfo(BaseModel):
#     time: datetime
#     content: Optional[str] = None
#     location: Optional[str] = None

# # 予定提案APIのリクエストボディ
# class SuggestionRequest(BaseModel):
#     free_time_start: datetime
#     free_time_end: datetime
#     prev_event: Optional[AdjacentEventInfo] = None
#     next_event: Optional[AdjacentEventInfo] = None

# # 提案結果のスキーマ
# class Suggestion(BaseModel):
#     title: str
#     description: str
#     link: Optional[str] = None
    
#     # snippet: str

# # 予定提案APIのレスポンス
# class SuggestionResponse(BaseModel):
#     query: str
#     suggestions: list[Suggestion]