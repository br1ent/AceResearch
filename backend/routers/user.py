from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from schemas.user.login.login import UserLogin
from services.user.loginService import LoginService
from utils.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/user", tags=["用户"])


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    photo: str

    class Config:
        from_attributes = True


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


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需要 JWT）"""
    return current_user
