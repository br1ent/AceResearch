"""知识库文档模型"""
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="文件名")
    file_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="文件类型: pdf/txt/md/docx")
    file_size: Mapped[int] = mapped_column(Integer, default=0, comment="文件大小(字节)")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="分块数")
    status: Mapped[str] = mapped_column(String(16), default="processing", comment="状态: processing/completed/failed")

    def __repr__(self):
        return f"<KnowledgeDocument {self.id} {self.title}>"
