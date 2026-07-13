"""对话 CRUD 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from schemas.chat import ConversationCreate, ConversationOut, MessageOut
from models.chat import Conversation as ConvModel
from models.project import Report, Source
from services.chat import ConversationService

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/conversations")
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新对话"""
    service = ConversationService(db)
    conv = service.create(user_id=current_user.id, title=body.title)
    return {"success": True, "data": ConversationOut.model_validate(conv)}


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话列表"""
    service = ConversationService(db)
    convs = service.list_by_user(user_id=current_user.id)
    return {
        "success": True,
        "data": [ConversationOut.model_validate(c) for c in convs],
    }


@router.get("/conversations/{conv_id}/messages")
def get_messages_api(
    conv_id: int,
    offset: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话消息历史（默认最近 30 条，支持分页）"""
    service = ConversationService(db)
    conv = service.get_by_id(conv_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    msgs = service.get_messages(conv_id, limit=limit, offset=offset)
    return {"success": True, "data": [MessageOut.model_validate(m) for m in msgs]}


@router.get("/conversations/search")
def search_conversations(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜索用户的对话"""
    convs = (
        db.query(ConvModel)
        .filter(ConvModel.user_id == current_user.id, ConvModel.title.contains(q))
        .order_by(ConvModel.update_at.desc())
        .all()
    )
    return {"success": True, "data": [ConversationOut.model_validate(c) for c in convs]}


@router.get("/conversations/{conv_id}/report")
def get_report(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话的最新研究报告"""
    service = ConversationService(db)
    conv = service.get_by_id(conv_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    report = db.query(Report).filter(Report.conversation_id == conv_id).order_by(Report.id.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="该对话暂无报告")

    sources = db.query(Source).filter(Source.report_id == report.id).order_by(Source.index).all()
    return {
        "success": True,
        "data": {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "status": report.status,
            "created_at": report.create_at.isoformat() if report.create_at else None,
            "sources": [{"index": s.index, "title": s.title, "url": s.url, "snippet": s.snippet} for s in sources],
        },
    }


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除对话（会级联删除消息和报告）"""
    service = ConversationService(db)
    if not service.delete(conv_id, current_user.id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"success": True, "message": "对话已删除"}
