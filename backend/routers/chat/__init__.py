"""Chat 路由聚合"""
from fastapi import APIRouter
from routers.chat.conversations import router as conv_router
from routers.chat.research import router as research_router

router = APIRouter()
router.include_router(conv_router)
router.include_router(research_router)
