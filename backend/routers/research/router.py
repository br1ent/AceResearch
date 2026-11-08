"""消息发送路由（研究模式端点）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from utils.user_llm import require_deepseek_key
from schemas.chat.chat import SendMessageRequest
from services.chat import ConversationService
from services.research.service import ResearchService

router = APIRouter(prefix="/api/chat", tags=["研究"])


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送研究消息（启动研究模式）"""
    require_deepseek_key(current_user.id)

    conv_service = ConversationService(db)

    # 1. 确定/创建对话 — 研究模式每个对话只研究一个话题
    if body.conversation_id:
        conv = conv_service.get_by_id(body.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
        # 如果当前对话已有研究记录，新建对话隔离话题
        from models.project import Report
        has_report = db.query(Report).filter(
            Report.conversation_id == conv.id,
            Report.status.in_(["completed", "generating", "awaiting_confirm"]),
        ).first()
        if has_report:
            title = body.message[:30] + ("..." if len(body.message) > 30 else "")
            conv = conv_service.create(
                user_id=current_user.id,
                title=title,
                mode=body.mode,
            )
    else:
        title = body.message[:30] + ("..." if len(body.message) > 30 else "")
        conv = conv_service.create(
            user_id=current_user.id,
            title=title,
            mode=body.mode,
        )

    # 2. 研究模式处理
    research_service = ResearchService(db)
    result = await research_service.start_research(
        conversation_id=conv.id,
        user_id=current_user.id,
        topic=body.message,
    )
    return result


@router.post("/research/confirm")
async def confirm_research(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户确认研究方案，开始执行研究"""
    require_deepseek_key(current_user.id)
    report_id = body.get("report_id")
    conversation_id = body.get("conversation_id")
    if not report_id or not conversation_id:
        raise HTTPException(status_code=400, detail="缺少 report_id 或 conversation_id")

    conv_service = ConversationService(db)
    conv = conv_service.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    research_service = ResearchService(db)
    return await research_service.confirm_and_execute(
        conversation_id=conversation_id,
        user_id=current_user.id,
        report_id=report_id,
    )


@router.post("/research/revise")
async def revise_research_plan(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户修改研究方案"""
    require_deepseek_key(current_user.id)
    report_id = body.get("report_id")
    conversation_id = body.get("conversation_id")
    feedback = body.get("feedback", "").strip()
    if not report_id or not conversation_id:
        raise HTTPException(status_code=400, detail="缺少 report_id 或 conversation_id")
    if not feedback:
        raise HTTPException(status_code=400, detail="请填写修改意见")

    conv_service = ConversationService(db)
    conv = conv_service.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    research_service = ResearchService(db)
    return await research_service.revise_plan(
        conversation_id=conversation_id,
        user_id=current_user.id,
        report_id=report_id,
        feedback=feedback,
    )
