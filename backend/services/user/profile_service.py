import os
import uuid

from sqlalchemy.orm import Session

from models.user import User

AVATAR_DIR = "media/avatars"


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def upload_avatar(self, user: User, file_data: bytes, filename: str) -> dict:
        old_photo = user.photo
        if old_photo and old_photo.startswith("/media/avatars/"):
            old_path = os.path.join(AVATAR_DIR, os.path.basename(old_photo))
            if os.path.exists(old_path):
                os.remove(old_path)

        ext = os.path.splitext(filename)[1] or ".png"
        new_name = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(AVATAR_DIR, exist_ok=True)
        with open(os.path.join(AVATAR_DIR, new_name), "wb") as f:
            f.write(file_data)

        user.photo = f"/media/avatars/{new_name}"
        self.db.commit()

        return {
            "success": True,
            "data": {"photo": user.photo},
        }

    def update_profile(self, user: User, username: str, email: str) -> dict:
        if not username or not username.strip():
            return {"success": False, "message": "用户名不能为空"}
        if len(username) > 20:
            return {"success": False, "message": "用户名不能超过20个字符"}
        if not email or not email.strip():
            return {"success": False, "message": "邮箱不能为空"}
        if len(email) > 50:
            return {"success": False, "message": "邮箱不能超过50个字符"}

        existing = self.db.query(User).filter(
            User.username == username, User.id != user.id
        ).first()
        if existing:
            return {"success": False, "message": "该用户名已被占用!"}

        existing = self.db.query(User).filter(
            User.email == email, User.id != user.id
        ).first()
        if existing:
            return {"success": False, "message": "该邮箱已被注册!"}

        user.username = username
        user.email = email
        self.db.commit()
        self.db.refresh(user)

        return {
            "success": True,
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "photo": user.photo,
                "create_at": user.create_at.isoformat() if user.create_at else None,
                "update_at": user.update_at.isoformat() if user.update_at else None,
            },
        }
