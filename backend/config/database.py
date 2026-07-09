from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    create_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="更新时间"
    )

def get_db():
    """获取数据库会话的依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
