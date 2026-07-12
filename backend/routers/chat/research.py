"""消息发送路由（统一入口：闲聊/研究模式）"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from schemas.chat import SendMessageRequest
from services.chat import ConversationService
from services.chat.chat_service import ChatService
from services.chat.research import ResearchService

router = APIRouter(prefix="/api/chat", tags=["消息"])


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息（根据 mode 自动选择闲聊模式或研究模式）"""
    conv_service = ConversationService(db)

    # 1. 确定/创建对话
    if body.conversation_id:
        conv = conv_service.get_by_id(body.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        title = body.message[:30] + ("..." if len(body.message) > 30 else "")
        conv = conv_service.create(
            user_id=current_user.id,
            title=title,
            mode=body.mode,
        )

    # 2. 根据模式处理
    if body.mode == "chat":
        chat_service = ChatService(db)
        reply = await chat_service.chat(conv.id, body.message)
        return {
            "success": True,
            "data": {
                "conversation_id": conv.id,
                "mode": "chat",
                "reply": reply,
            },
        }
    else:
        # research 模式
        research_service = ResearchService(db)
        result = await research_service.start_research(
            conversation_id=conv.id,
            user_id=current_user.id,
            topic=body.message,
        )
        return result


@router.post("/send/stream")
async def send_message_stream(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """闲聊流式输出（SSE）"""
    conv_service = ConversationService(db)

    # 确定/创建对话
    if body.conversation_id:
        conv = conv_service.get_by_id(body.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        title = body.message[:30] + ("..." if len(body.message) > 30 else "")
        conv = conv_service.create(user_id=current_user.id, title=title, mode="chat")

    chat_service = ChatService(db)

    async def event_stream():
        # 首条消息：发送 conversation_id
        first = json.dumps({"type": "meta", "conversation_id": conv.id}, ensure_ascii=False)
        yield f"data: {first}\n\n"

        # 逐 token 推送
        async for token in chat_service.chat_stream(conv.id, body.message):
            yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

        # 结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/research/confirm")
async def confirm_research(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户确认研究方案，开始执行研究"""
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
