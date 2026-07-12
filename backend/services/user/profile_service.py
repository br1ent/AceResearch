import os
import uuid
import io

from PIL import Image
from sqlalchemy.orm import Session

from models.user import User

AVATAR_DIR = "media/avatars"


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def upload_avatar(self, user: User, file_data: bytes, filename: str,
                      crop_x: int = 0, crop_y: int = 0,
                      crop_w: int = 0, crop_h: int = 0) -> dict:
        img = Image.open(io.BytesIO(file_data))

        # 裁剪
        if crop_w > 0 and crop_h > 0:
            img = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))

        # 缩放为正方形 200x200
        img = img.convert("RGB")
        size = min(img.size)
        left = (img.size[0] - size) // 2
        top = (img.size[1] - size) // 2
        img = img.crop((left, top, left + size, top + size))
        img = img.resize((200, 200), Image.LANCZOS)

        # 删除旧头像
        old_photo = user.photo
        if old_photo and old_photo.startswith("/media/avatars/"):
            old_path = os.path.join(AVATAR_DIR, os.path.basename(old_photo))
            if os.path.exists(old_path):
                os.remove(old_path)

        # 保存新头像
        ext = os.path.splitext(filename)[1] or ".png"
        new_name = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(AVATAR_DIR, exist_ok=True)
        img.save(os.path.join(AVATAR_DIR, new_name))

        user.photo = f"/media/avatars/{new_name}"
        self.db.commit()

        return {
            "success": True,
            "data": {"photo": user.photo},
        }

    def update_profile(self, user: User, username: str, email: str) -> dict:
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
