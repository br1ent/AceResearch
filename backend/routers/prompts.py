"""提示词管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from models.agent_prompt import AgentPrompt

router = APIRouter(prefix="/api/prompts", tags=["提示词"])


class PromptUpdate(BaseModel):
    content: str = Field(..., min_length=1)


@router.get("")
def list_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有提示词"""
    prompts = db.query(AgentPrompt).order_by(AgentPrompt.mode, AgentPrompt.stage).all()
    return {
        "success": True,
        "data": [
            {"id": p.id, "mode": p.mode, "stage": p.stage, "content": p.content, "description": p.description}
            for p in prompts
        ],
    }


@router.put("/{prompt_id}")
def update_prompt(
    prompt_id: int,
    body: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新指定提示词"""
    prompt = db.query(AgentPrompt).filter(AgentPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    prompt.content = body.content
    db.commit()
    return {"success": True, "message": "提示词已更新"}


@router.get("/{prompt_id}")
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个提示词详情"""
    prompt = db.query(AgentPrompt).filter(AgentPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "data": {"id": prompt.id, "mode": prompt.mode, "stage": prompt.stage, "content": prompt.content, "description": prompt.description}}
