from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from config.settings import get_settings
from config.database import engine, Base
from routers.chat import router as chat_router
from routers.chat.stream import router as chat_stream_router
from routers.chat.reports import router as reports_router
from routers.research.router import router as research_router
from routers.user import router as user_router
from routers.prompts import router as prompts_router
from routers.ws import router as ws_router
from routers.knowledge_base.documents import router as kb_router

settings = get_settings()

app = FastAPI(
    title="AceResearch API",
    description="AceResearch 研思 - 多 Agent 协作深度研究平台",
    version="1.0.0"
)

# API 路由
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(chat_stream_router)
app.include_router(research_router)
app.include_router(reports_router)
app.include_router(prompts_router)
app.include_router(ws_router)
app.include_router(kb_router)

# 前端构建产物 — 静态文件
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# 媒体文件（头像等）
app.mount("/media", StaticFiles(directory="media"), name="media")


# 图标
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(FRONTEND_DIST / "favicon.ico"))

# SPA 兜底：未匹配路径返回 index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(str(FRONTEND_DIST / "index.html"))


@app.on_event("startup")
def startup():
    """启动时初始化数据库表"""
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
