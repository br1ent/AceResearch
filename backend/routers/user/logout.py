from fastapi import APIRouter, Response

from services.user.logout_service import LogoutService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/logout")
async def logout(response: Response):
    service = LogoutService()
    result = service.logout()

    response.delete_cookie(key="refresh_token")

    return result
