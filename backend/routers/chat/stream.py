"""闲聊流式输出路由（SSE）"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from schemas.chat.chat import SendMessageRequest
from services.chat import ConversationService
from services.chat.service import ChatService

router = APIRouter(prefix="/api/chat", tags=["闲聊"])


@router.post("/send/stream")
async def send_message_stream(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """闲聊流式输出（SSE）"""
    conv_service = ConversationService(db)

    mode = body.mode or "chat"

    # 确定/创建对话
    if body.conversation_id:
        conv = conv_service.get_by_id(body.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        title = body.message[:30] + ("..." if len(body.message) > 30 else "")
        conv = conv_service.create(user_id=current_user.id, title=title, mode=mode)

    chat_service = ChatService(db)

    async def event_stream():
        # 首条消息：发送 conversation_id
        first = json.dumps({"type": "meta", "conversation_id": conv.id}, ensure_ascii=False)
        yield f"data: {first}\n\n"

        # 逐 token 推送
        async for token in chat_service.chat_stream(conv.id, body.message, mode):
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
