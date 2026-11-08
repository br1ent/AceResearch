from fastapi import APIRouter, Body, Depends, UploadFile, File, Form

from models.user import User
from utils.auth import get_current_user
from services.user.profile_service import ProfileService
from config.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    return service.upload_avatar(
        current_user,
        await file.read(),
        file.filename or "avatar.png",
    )


@router.put("/profile")
async def update_profile(
    username: str = Form(...),
    email: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ProfileService(db)
    return service.update_profile(current_user, username, email)


@router.get("/apikeys")
async def get_apikeys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户 API Key 配置状态（掩码）和只读模型名"""
    service = ProfileService(db)
    return service.get_apikeys(current_user)


@router.post("/apikeys")
async def update_apikeys(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存用户 API Key"""
    service = ProfileService(db)
    return service.update_apikeys(current_user, payload)


@router.post("/apikeys/delete")
async def delete_apikeys(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清除用户 API Key（payload: {"fields": [...]}）"""
    service = ProfileService(db)
    return service.delete_apikeys(current_user, payload.get("fields") or [])
