from sqlalchemy.orm import Session

from models.user import User
from schemas.user.reset_pwd import UserResetPwd
from utils.auth import hash_password


class ResetPwdService:
    def __init__(self, db: Session):
        self.db = db

    def reset_password(self, form: UserResetPwd) -> dict:
        if form.password != form.confirm_password:
            return {
                "success": False,
                "message": "两次输入的密码不一致!",
            }

        user = self.db.query(User).filter(
            User.username == form.username,
            User.email == form.email,
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户名或邮箱不匹配!",
            }

        user.password_hash = hash_password(form.password)
        self.db.commit()

        return {
            "success": True,
            "message": "密码重置成功!",
        }
