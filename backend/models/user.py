import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func


class User:
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    photo = Column(String(100), default="")
    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
