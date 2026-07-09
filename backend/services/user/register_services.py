from sqlalchemy.orm import Session

from models.user import User
from schemas.user.register import UserRegister
from utils.auth import hash_password


class RegisterServices:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, form: UserRegister) -> dict:
        if form.password != form.confirm_password:
            return {
                "success": False,
                "message": "两次密码不一致!"
            }

        if self.db.query(User).filter(User.email == form.email).first():
            return {
                "success": False,
                "message": "该邮箱已被注册!"
            }

        if self.db.query(User).filter(User.username == form.username).first():
            return {
                "success": False,
                "message": "该用户名已被占用!"
            }


        user = User(
            username=form.username,
            email=form.email,
            password_hash=hash_password(form.password),
            photo="/static/avatars/default.png",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return {
            "success": True,
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "photo": "/static/user/avatar/default.png",
            },
        }
