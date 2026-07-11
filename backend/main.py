from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.settings import get_settings
from config.database import engine, Base
from routers.user import router as user_router

settings = get_settings()

app = FastAPI(
    title="Smart Research Assistant API",
    description="智能研究助手后端API",
    version="1.0.0"
)

# API 路由
app.include_router(user_router)

# 后端静态文件（头像等）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 前端 SPA（未匹配的路由全部回退到 index.html）
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")


@app.on_event("startup")
def startup():
    """启动时初始化数据库表"""
    Base.metadata.create_all(bind=engine)
