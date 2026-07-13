"""Agent 提示词模型：研究模式/闲聊模式各有独立的系统提示词"""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer

from config.database import Base


class AgentPrompt(Base):
    """可配置的 Agent 系统提示词"""
    __tablename__ = "agent_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="提示词ID")
    mode: Mapped[str] = mapped_column(String(20), nullable=False, comment="模式: chat / research")
    stage: Mapped[str] = mapped_column(
        String(30), default="system",
        comment="阶段: system / planner / researcher / analyst / writer / reviewer"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="提示词内容")
    description: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="说明（方便识别）")

    def __repr__(self) -> str:
        return f"<AgentPrompt {self.id} mode={self.mode} stage={self.stage}>"
