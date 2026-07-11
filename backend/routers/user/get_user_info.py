from fastapi import APIRouter, Depends

from models.user import User
from utils.auth import get_current_user
from services.user.get_user_info_services import GetUserInfoServices

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/me")
async def get_user_info(current_user: User = Depends(get_current_user)):
    service = GetUserInfoServices()
    return service.get_user_info(current_user)
