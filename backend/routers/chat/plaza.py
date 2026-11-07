"""报告广场路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config.database import get_db
from models.chat import Conversation
from models.plaza import ReportLike, ReportShare
from models.project import Report
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/api/plaza", tags=["报告广场"])


def _get_owned_report(db: Session, report_id: int, user_id: int) -> Report:
    report = (
        db.query(Report)
        .join(Conversation, Report.conversation_id == Conversation.id)
        .filter(Report.id == report_id, Conversation.user_id == user_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


@router.get("/reports")
def list_plaza_reports(
    keyword: str = Query(default="", description="搜索报告标题或作者名称"),
    sort: str = Query(default="likes", pattern="^(likes|date)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """广场报告列表，支持标题/作者搜索，按点赞量或发布日期排序"""
    query = db.query(ReportShare, User.username).join(User, ReportShare.publisher_id == User.id)

    keyword = keyword.strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(ReportShare.title.like(like), User.username.like(like)))

    if sort == "likes":
        query = query.order_by(ReportShare.like_count.desc(), ReportShare.create_at.desc())
    else:
        query = query.order_by(ReportShare.create_at.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    share_ids = [share.id for share, _ in rows]
    liked_ids = set()
    if share_ids:
        liked_ids = {
            like.share_id
            for like in db.query(ReportLike)
            .filter(ReportLike.share_id.in_(share_ids), ReportLike.user_id == current_user.id)
            .all()
        }

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": share.id,
                    "title": share.title,
                    "author": username,
                    "like_count": share.like_count,
                    "liked": share.id in liked_ids,
                    "published_at": share.create_at.isoformat() if share.create_at else None,
                }
                for share, username in rows
            ],
        },
    }


@router.get("/reports/{share_id}")
def get_plaza_report_detail(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """广场报告详情"""
    row = (
        db.query(ReportShare, Report, User.username)
        .join(Report, ReportShare.report_id == Report.id)
        .join(User, ReportShare.publisher_id == User.id)
        .filter(ReportShare.id == share_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="分享不存在或已取消发布")
    share, report, username = row

    liked = (
        db.query(ReportLike)
        .filter(ReportLike.share_id == share.id, ReportLike.user_id == current_user.id)
        .first()
        is not None
    )

    return {
        "success": True,
        "data": {
            "id": share.id,
            "title": share.title,
            "content": report.content,
            "author": username,
            "like_count": share.like_count,
            "liked": liked,
            "published_at": share.create_at.isoformat() if share.create_at else None,
        },
    }


@router.post("/reports/{share_id}/like")
def toggle_like(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """点赞 / 取消点赞"""
    share = db.query(ReportShare).filter(ReportShare.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在或已取消发布")

    existing = (
        db.query(ReportLike)
        .filter(ReportLike.share_id == share_id, ReportLike.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        share.like_count = max(0, share.like_count - 1)
        liked = False
    else:
        db.add(ReportLike(share_id=share_id, user_id=current_user.id))
        share.like_count += 1
        liked = True
    db.commit()
    return {"success": True, "data": {"liked": liked, "like_count": share.like_count}}


@router.post("/publish/{report_id}")
def publish_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将报告发布到广场"""
    report = _get_owned_report(db, report_id, current_user.id)

    share = db.query(ReportShare).filter(ReportShare.report_id == report_id).first()
    if share:
        return {"success": True, "data": {"share_id": share.id, "already": True}}

    share = ReportShare(report_id=report.id, publisher_id=current_user.id, title=report.title)
    db.add(share)
    db.commit()
    db.refresh(share)
    return {"success": True, "data": {"share_id": share.id, "already": False}, "message": "已发布到报告广场"}


@router.delete("/publish/{report_id}")
def unpublish_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从广场取消发布"""
    report = _get_owned_report(db, report_id, current_user.id)

    share = db.query(ReportShare).filter(ReportShare.report_id == report.id).first()
    if not share:
        raise HTTPException(status_code=404, detail="该报告尚未发布")
    db.query(ReportLike).filter(ReportLike.share_id == share.id).delete()
    db.delete(share)
    db.commit()
    return {"success": True, "message": "已从广场取消发布"}
