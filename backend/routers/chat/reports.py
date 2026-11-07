"""报告路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from models.project import Report
from utils.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["报告"])


@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户的所有报告"""
    from models.chat import Conversation
    from models.plaza import ReportShare
    reports = (
        db.query(Report)
        .join(Conversation, Report.conversation_id == Conversation.id)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Report.create_at.desc())
        .all()
    )
    shared_map = {
        s.report_id: s.id
        for s in db.query(ReportShare).filter(ReportShare.report_id.in_([r.id for r in reports])).all()
    } if reports else {}
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "reviewer_rewrite_count": r.reviewer_rewrite_count,
                "created_at": r.create_at.isoformat() if r.create_at else None,
                "shared": r.id in shared_map,
                "share_id": shared_map.get(r.id),
            }
            for r in reports
        ],
    }


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除报告"""
    from models.chat import Conversation
    report = (
        db.query(Report)
        .join(Conversation, Report.conversation_id == Conversation.id)
        .filter(Report.id == report_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    from models.plaza import ReportLike, ReportShare
    share = db.query(ReportShare).filter(ReportShare.report_id == report.id).first()
    if share:
        db.query(ReportLike).filter(ReportLike.share_id == share.id).delete()
        db.delete(share)
    db.delete(report)
    db.commit()
    return {"success": True, "message": "报告已删除"}


@router.get("/{report_id}")
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报告详情"""
    import json as _json
    from models.chat import Conversation
    report = (
        db.query(Report)
        .join(Conversation, Report.conversation_id == Conversation.id)
        .filter(Report.id == report_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    review_log = None
    if report.review_log:
        try:
            review_log = _json.loads(report.review_log)
        except _json.JSONDecodeError:
            review_log = None

    return {
        "success": True,
        "data": {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "status": report.status,
            "reviewer_rewrite_count": report.reviewer_rewrite_count,
            "review_log": review_log,
            "created_at": report.create_at.isoformat() if report.create_at else None,
            },
        }
