from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, time

from .. import schemas, crud
from ..database import get_db
from ..user_profile import UserProfileService

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=schemas.UserProfileResponse)
async def get_user_profile(db: AsyncSession = Depends(get_db)):
    """
    ユーザープロフィールを取得します。
    プロフィールが古い、かつ本日新しい予定が追加/更新されている場合にのみ、プロフィールを再生成します。
    """
    latest_profile = await crud.get_latest_user_profile(db)
    today = date.today()

    # プロフィールが存在し、かつ今日生成されたものであれば、それを返す
    if latest_profile and latest_profile.created_at.date() >= today:
        return latest_profile

    # プロフィールが古いか、存在しない場合
    # 今日の開始時刻（00:00:00）を取得
    start_of_today = datetime.combine(today, time.min)

    # プロフィールが古い場合は、今日更新された予定があるかチェック
    if latest_profile:
        events_updated_today = await crud.has_events_updated_since(db, since=start_of_today)
        if not events_updated_today:
            # 今日の更新がなければ、古いプロフィールのままでOK
            return latest_profile

    # プロフィールが存在しない、またはプロフィールが古く今日の更新があった場合に再生成
    try:
        new_profile = await UserProfileService.generate_profile(db)
        return new_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate profile: {e}"
        )
