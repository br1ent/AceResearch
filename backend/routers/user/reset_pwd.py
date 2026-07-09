from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from schemas.user.reset_pwd import UserResetPwd
from services.user.reset_pwd_services import ResetPwdService

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/reset-password")
async def reset_password(form: UserResetPwd, db: Session = Depends(get_db)):
    service = ResetPwdService(db)
    return service.reset_password(form)
