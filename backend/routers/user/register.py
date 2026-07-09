from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from schemas.user.register import UserRegister
from services.user.register_services import RegisterServices

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/register")
async def register(form: UserRegister, db: Session = Depends(get_db)):
    service = RegisterServices(db)
    result = service.register_user(form)
    return result
