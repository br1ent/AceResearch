from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from schemas.user.login.login import UserLogin
from services.user.loginService import LoginService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/login")
def login(form: UserLogin, db: Session = Depends(get_db)):
    service = LoginService(db)
    result = service.login(form)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["detail"]
        )

    return result["data"]
