from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
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
    最近の予定履歴からユーザーの傾向を分析し、プロフィールを生成します。
    """
    try:
        profile_text = await UserProfileService.generate_profile(db)
        return schemas.UserProfileResponse(profile=profile_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate profile: {e}"
        )
