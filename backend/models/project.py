from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer, DateTime

from config.database import Base


class Report(Base):
    """研究报告"""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="报告ID")
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="所属对话ID"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="报告标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="报告内容(Markdown)")
    status: Mapped[str] = mapped_column(
        String(20), default="draft", comment="状态: generating / draft / completed / failed"
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} title={self.title} status={self.status}>"


class Source(Base):
    """引用来源"""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="来源ID")
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, comment="所属报告ID"
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False, comment="引用编号")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    url: Mapped[str] = mapped_column(String(500), nullable=False, comment="URL")
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True, comment="摘要")
