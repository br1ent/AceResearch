from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer, DateTime

from config.database import Base


class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="对话ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户ID"
    )
    title: Mapped[str] = mapped_column(String(100), default="新对话", comment="对话标题")
    mode: Mapped[str] = mapped_column(String(20), default="research", comment="模式: chat / research / knowledge")

    def __repr__(self) -> str:
        return f"<Conversation {self.id} user={self.user_id} mode={self.mode} title={self.title}>"


class Message(Base):
    """对话消息"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="所属对话ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户ID"
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色: user / assistant / system")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    msg_type: Mapped[str] = mapped_column(
        String(30), default="text",
        comment="消息类型: text / agent_status / search_result / report / error"
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="附加元数据(JSON)")

    def __repr__(self) -> str:
        return f"<Message {self.id} conv={self.conversation_id} user={self.user_id} role={self.role}>"
