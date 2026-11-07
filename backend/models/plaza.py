"""报告广场模型"""
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer

from config.database import Base


class ReportShare(Base):
    """发布到广场的报告"""
    __tablename__ = "report_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分享ID")
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False, comment="报告ID"
    )
    publisher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="发布者ID"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="发布时的报告标题快照")
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="点赞数")

    def __repr__(self) -> str:
        return f"<ReportShare {self.id} report={self.report_id} title={self.title}>"


class ReportLike(Base):
    """广场报告点赞记录"""
    __tablename__ = "report_likes"
    __table_args__ = (
        UniqueConstraint("share_id", "user_id", name="uq_report_like_share_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="点赞ID")
    share_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("report_shares.id", ondelete="CASCADE"), nullable=False, comment="分享ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="点赞用户ID"
    )

    def __repr__(self) -> str:
        return f"<ReportLike {self.id} share={self.share_id} user={self.user_id}>"
