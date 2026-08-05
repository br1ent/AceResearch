from datetime import datetime, timedelta, timezone
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import get_settings
from utils.redis import get_redis

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

_redis = get_redis()

BCRYPT_LIMIT = 72


def _cache_user(user) -> None:
    """将用户关键字段写入 Redis，TTL 5 分钟"""
    import json
    photo = user.photo or ""
    if photo.startswith("/"):
        photo = f"{settings.BASE_URL}{photo}"
    _redis.setex(
        f"user:{user.id}",
        300,
        json.dumps({"id": user.id, "email": user.email, "username": user.username, "photo": photo}),
    )


def invalidate_user_cache(user_id: int) -> None:
    """用户信息变更时清除缓存"""
    _redis.delete(f"user:{user_id}")


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:BCRYPT_LIMIT])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:BCRYPT_LIMIT], hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    user_id = str(data.get("sub", ""))
    _redis.setex(f"token:{jti}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, user_id)
    return token


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    user_id = str(data.get("sub", ""))
    _redis.setex(f"token:{jti}", settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, user_id)
    return token


def revoke_user_tokens(user_id: int) -> None:
    """注销用户所有 token（删除 Redis 中的 token 记录）"""
    pattern = f"token:*"
    cursor = 0
    while True:
        cursor, keys = _redis.scan(cursor, match=pattern, count=100)
        for key in keys:
            if _redis.get(key) == str(user_id):
                _redis.delete(key)
        if cursor == 0:
            break


def decode_token(token: str) -> dict | None:
    """解码 JWT token，校验签名、过期、以及 Redis 黑名单"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

    jti = payload.get("jti")
    if not jti or not _redis.exists(f"token:{jti}"):
        return None

    return payload


def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """同 get_current_user，但 token 无效时返回 None 而非 401"""
    import json
    from types import SimpleNamespace
    from models.user import User

    payload = decode_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    cached = _redis.get(f"user:{user_id}")
    if cached:
        data = json.loads(cached)
        return SimpleNamespace(id=data["id"], email=data["email"], username=data["username"], photo=data.get("photo", ""))

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        return None

    _cache_user(user)
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """从 JWT 中解析当前用户（带 Redis 缓存 + 黑名单校验）"""
    import json
    from types import SimpleNamespace
    from models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # P1: 先查 Redis 缓存
    cached = _redis.get(f"user:{user_id}")
    if cached:
        data = json.loads(cached)
        return SimpleNamespace(id=data["id"], email=data["email"], username=data["username"], photo=data.get("photo", ""))

    # 未命中 → 查 DB 并写入缓存
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    _cache_user(user)
    return user
