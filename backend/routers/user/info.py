from fastapi import APIRouter, Depends

from models.user import User
from utils.auth import get_current_user
from services.user.user_info_service import UserInfoService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/me")
async def get_user_info(current_user: User = Depends(get_current_user)):
    service = UserInfoService()
    return service.get_user_info(current_user)
