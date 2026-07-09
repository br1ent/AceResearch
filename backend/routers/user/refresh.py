from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.user.refresh_service import RefreshService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/refresh")
async def refresh(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    auth_header = request.headers.get("Authorization")

    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[len("Bearer "):]

    service = RefreshService()
    result = service.refresh(refresh_token, access_token)

    if not result["success"]:
        return JSONResponse(
            status_code=result.get("status_code", 200),
            content=result,
        )

    return result
