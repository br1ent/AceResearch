from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer, Text

from config.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer ,primary_key=True, autoincrement=True, comment="用户id")
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="邮箱")
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="用户名")
    password_hash: Mapped[str] = mapped_column(String(100), comment="用户加密的密码")
    photo: Mapped[str] = mapped_column(String(100), comment="用户头像的url")
    memory: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="", comment="用户记忆JSON")

    def __repr__(self) -> str:
        return f"<{self.id} {self.username} {self.email}>"