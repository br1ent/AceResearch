from sqlalchemy.orm import Session

from models.user import User
from schemas.user.login import UserLogin
from utils.auth import verify_password, create_access_token, create_refresh_token


class LoginService:
    def __init__(self, db: Session):
        self.db = db

    def login(self, form: UserLogin) -> dict:
        user = self.db.query(User).filter(User.email == form.email).first()

        if not user:
            return {
                "success": False,
                "message": "用户还没注册!"
            }

        if not verify_password(form.password, user.password_hash):
            return {
                "success": False,
                "message": "密码错误!"
            }

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "photo": user.photo,
                }
            }
        }
