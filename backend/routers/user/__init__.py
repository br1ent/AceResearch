from routers.user.login import router as login_router
from routers.user.register import router as register_router
from routers.user.refresh import router as refresh_router
from routers.user.logout import router as logout_router
from routers.user.reset_pwd import router as reset_pwd_router
from routers.user.get_user_info import router as get_user_info
from fastapi import APIRouter

router = APIRouter()
router.include_router(login_router)
router.include_router(register_router)
router.include_router(refresh_router)
router.include_router(logout_router)
router.include_router(reset_pwd_router)
router.include_router(get_user_info)
