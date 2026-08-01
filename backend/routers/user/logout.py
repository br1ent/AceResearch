from fastapi import APIRouter, Depends, Response

from models.user import User
from services.user.logout_service import LogoutService
from utils.auth import get_current_user_optional

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/logout")
async def logout(response: Response, current_user: User | None = Depends(get_current_user_optional)):
    service = LogoutService()
    user_id = current_user.id if current_user else None
    result = service.logout(user_id=user_id)
    response.delete_cookie(key="refresh_token")
    return result
