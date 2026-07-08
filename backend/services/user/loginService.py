from sqlalchemy.orm import Session

from models.user import User
from schemas.user.login.login import UserLogin
from utils.auth import verify_password, create_access_token, create_refresh_token


class LoginService:
    def __init__(self, db: Session):
        self.db = db

    def login(self, form: UserLogin) -> dict:
        """用户登录"""
        user = self.db.query(User).filter(User.username == form.username).first()
        if not user or not verify_password(form.password, user.hashed_password):
            return {"success": False, "detail": "用户名或密码错误"}

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "photo": user.photo,
                }
            }
        }
