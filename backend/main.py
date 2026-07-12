from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from config.settings import get_settings
from config.database import engine, Base, SessionLocal
from routers.chat import router as chat_router
from routers.user import router as user_router
from websocket import manager as ws_manager
from utils.auth import decode_token

settings = get_settings()

app = FastAPI(
    title="Smart Research Assistant API",
    description="智能研究助手后端API",
    version="1.0.0"
)

# API 路由
app.include_router(user_router)
app.include_router(chat_router)

# 媒体文件（头像等）
app.mount("/media", StaticFiles(directory="media"), name="media")

# 前端构建产物
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


# SPA 兜底：所有未匹配的路径都返回 index.html（Vue Router 接管）
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(str(FRONTEND_DIST / "index.html"))


@app.websocket("/ws/{conversation_id}")
async def research_websocket(websocket: WebSocket, conversation_id: int, token: str = Query(...)):
    """研究进度 WebSocket 实时推送（需 token 验证用户）"""
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="token无效")
        return

    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.close(code=4001, reason="token无效")
        return

    # 验证对话属于当前用户
    from models.chat import Conversation
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == int(user_id_str),
        ).first()
        if not conv:
            await websocket.close(code=4003, reason="无权访问该对话")
            return
    finally:
        db.close()

    await ws_manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(conversation_id, websocket)
    except Exception:
        ws_manager.disconnect(conversation_id, websocket)


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(FRONTEND_DIST / "favicon.ico"))


@app.on_event("startup")
def startup():
    """启动时初始化数据库表并填充默认提示词"""
    import models  # noqa: F401  确保所有模型被加载
    Base.metadata.create_all(bind=engine)

    from config.database import SessionLocal
    from models.agent_prompt import seed_default_prompts
    db = SessionLocal()
    try:
        seed_default_prompts(db)
    finally:
        db.close()
