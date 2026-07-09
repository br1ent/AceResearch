from fastapi.responses import Response
from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from config.database import get_db
from schemas.user.login import UserLogin
from services.user.login_services import LoginService

router = APIRouter(prefix="/api/user", tags=["用户"])

@router.post("/login")
async def login(form: UserLogin, response: Response, db: Session = Depends(get_db)):

    service = LoginService(db)

    result = service.login(form)

    if result["success"]:
        response.set_cookie(
            key="refresh_token",
            value=result["data"]["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
        )

        return result

    return result
