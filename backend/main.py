from fastapi import FastAPI
from config.settings import get_settings
from config.database import engine, Base

settings = get_settings()

app = FastAPI(
    title="Smart Research Assistant API",
    description="智能研究助手后端API",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    """启动时初始化数据库表"""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}
