import os
import uuid

from sqlalchemy.orm import Session

from models.user import User
from config.settings import get_settings

settings = get_settings()
AVATAR_DIR = "media/avatars"


def _photo_url(photo: str) -> str:
    """将相对路径转为完整 URL，供 API 返回给前端"""
    if photo and photo.startswith("/"):
        return f"{settings.BASE_URL}{photo}"
    return photo


def _mask(value: str | None) -> str:
    """敏感信息掩码，只保留前 3 后 4 位"""
    if not value:
        return ""
    if len(value) <= 7:
        return "****"
    return f"{value[:3]}****{value[-4:]}"


APIKEY_FIELDS = ("deepseek_api_key", "dashscope_api_key", "dashscope_workspace_id")


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
        from utils.auth import invalidate_user_cache
        invalidate_user_cache(user.id)

        return {
            "success": True,
            "data": {"photo": _photo_url(user.photo)},
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
        from utils.auth import invalidate_user_cache
        invalidate_user_cache(user.id)
        self.db.refresh(user)

        return {
            "success": True,
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "photo": _photo_url(user.photo),
            },
        }

    def _get_db_user(self, user: User) -> User:
        """current_user 可能来自 Redis 缓存（非 ORM 对象），按 id 重新查询"""
        return self.db.query(User).filter(User.id == user.id).first()

    def get_apikeys(self, user: User) -> dict:
        """返回用户 API Key 配置状态（掩码，不回传明文）和只读模型名"""
        from config.agents import get_agent_settings
        from config.knowledge_base import get_kb_settings
        agent_settings = get_agent_settings()
        kb_settings = get_kb_settings()
        db_user = self._get_db_user(user) or user

        def item(value: str | None) -> dict:
            return {"configured": bool(value), "masked": _mask(value)}

        return {
            "success": True,
            "data": {
                "deepseek_api_key": item(getattr(db_user, "deepseek_api_key", None)),
                "dashscope_api_key": item(getattr(db_user, "dashscope_api_key", None)),
                "dashscope_workspace_id": item(getattr(db_user, "dashscope_workspace_id", None)),
                "models": {
                    "deepseek_model": agent_settings.DEEPSEEK_MODEL,
                    "embedding_model": kb_settings.EMBEDDING_MODEL,
                    "rerank_model": kb_settings.RERANK_MODEL,
                },
            },
        }

    def update_apikeys(self, user: User, keys: dict) -> dict:
        """保存用户 API Key（只更新传入的非 None 字段）"""
        db_user = self._get_db_user(user)
        if not db_user:
            return {"success": False, "message": "用户不存在"}
        for field in APIKEY_FIELDS:
            value = keys.get(field)
            if value is not None:
                setattr(db_user, field, value.strip())
        self.db.commit()
        from utils.auth import invalidate_user_cache
        from utils.user_llm import invalidate_user_llm
        invalidate_user_cache(user.id)
        invalidate_user_llm(user.id)
        return {"success": True, "message": "API Key 已保存"}

    def delete_apikeys(self, user: User, fields: list[str]) -> dict:
        """清除指定的 API Key 字段"""
        db_user = self._get_db_user(user)
        if not db_user:
            return {"success": False, "message": "用户不存在"}
        cleared = False
        for field in fields:
            if field in APIKEY_FIELDS:
                setattr(db_user, field, "")
                cleared = True
        if not cleared:
            return {"success": False, "message": "没有可清除的字段"}
        self.db.commit()
        from utils.auth import invalidate_user_cache
        from utils.user_llm import invalidate_user_llm
        invalidate_user_cache(user.id)
        invalidate_user_llm(user.id)
        return {"success": True, "message": "已清除"}
