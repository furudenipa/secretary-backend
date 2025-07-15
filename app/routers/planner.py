# app/routers/planner.py を修正

from fastapi import APIRouter, HTTPException, Depends # Dependsを追加
from sqlalchemy.ext.asyncio import AsyncSession       # AsyncSessionを追加
from .. import schemas, service, crud                # crudを追加
from ..database import get_db           # get_dbを追加
from zoneinfo import ZoneInfo # 標準ライブラリ zoneinfo をインポート

router = APIRouter(
    prefix="/planner",
    tags=["Planner"]
)

# ... 既存の /generate-plans エンドポイント ...
@router.post("/generate-plans", response_model=schemas.PlannerResponse)
async def generate_comprehensive_plans(request: schemas.MobilityRequest):
    try:
        full_plan = await service.MasterPlannerAgent.generate_plans(request)
        return full_plan
    except Exception as e:
        print(f"Error in planner endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plans.")

# --- ここから新しいエンドポイントを追加 ---
@router.post("/generate-plans-from-free-time", response_model=schemas.PlannerResponse)
async def generate_plans_from_free_time(
    request: schemas.ConveniencePlannerRequest,
    db: AsyncSession = Depends(get_db)
):
    """空き時間を指定すると、DBから直前・直後の予定を自動で補完してプランを生成します。"""
    
    # 1. DBから直前・直後のイベントを取得
    prev_event_db = await crud.get_previous_event(db, request.free_time_start)
    next_event_db = await crud.get_next_event(db, request.free_time_end)

    # 2. MasterPlannerAgentへの入力（MobilityRequest）を組み立てる
    # 直前のイベントが見つからなければ、ユーザーが指定した空き時間の開始時刻をそのまま使う
    prev_event_end_time = prev_event_db.end_time if prev_event_db else request.free_time_start
    prev_event_location = prev_event_db.location if prev_event_db else "現在地" # デフォルト値を設定

    # 直後のイベントが見つからなければ、ユーザーが指定した空き時間の終了時刻をそのまま使う
    next_event_start_time = next_event_db.start_time if next_event_db else request.free_time_end
    next_event_location = next_event_db.location if next_event_db else "特になし" # デフォルト値を設定
    
    print(next_event_start_time)
    print(prev_event_end_time)
    # 時間の前後関係が正しいかチェック
    # タイムゾーンをJSTに統一して、安全な比較を可能にする
    # JST = ZoneInfo("Asia/Tokyo")

    # タイムゾーン情報がない場合(naive)は、JSTとして扱う(awareにする)
    # if prev_event_end_time.tzinfo is None:
    #     prev_event_end_time = prev_event_end_time.replace()
    
    # if next_event_start_time.tzinfo is None:
    #     next_event_start_time = next_event_start_time.replace()

    # これで、aware同士の安全な比較になる
    # if prev_event_end_time >= next_event_start_time:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="検索されたイベントの時間関係が不正です。直前の予定が直後の予定より後に終了します。"
    #     )

    # AIエージェントに渡すためのリクエストオブジェクトを作成
    agent_request = schemas.MobilityRequest(
        prev_event_end_time=prev_event_end_time,
        prev_event_location=prev_event_location,
        next_event_start_time=next_event_start_time,
        next_event_location=next_event_location,
        user_preferences=request.user_preferences
    )

    # 3. MasterPlannerAgentを呼び出して、最終的なプランを生成
    try:
        full_plan = await service.MasterPlannerAgent.generate_plans(agent_request)
        return full_plan
    except Exception as e:
        print(f"Error in planner endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plans.")