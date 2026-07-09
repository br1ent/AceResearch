from routers.user.login import router as login_router
from routers.user.register import router as register_router
from routers.user.refresh import router as refresh_router
from routers.user.logout import router as logout_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(login_router)
router.include_router(register_router)
router.include_router(refresh_router)
router.include_router(logout_router)
