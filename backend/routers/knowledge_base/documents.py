"""知识库文档管理路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User
from utils.auth import get_current_user
from config.knowledge_base import get_kb_settings
from services.knowledge_base.document_service import (
    upload_and_process, list_documents, delete_document, get_document_count,
)

kb_settings = get_kb_settings()
router = APIRouter(prefix="/api/kb", tags=["知识库"])


@router.get("/documents/count")
async def doc_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户文档数量"""
    return {"success": True, "data": {"count": get_document_count(current_user.id)}}


@router.get("/documents")
async def list_docs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出用户文档"""
    return {"success": True, "data": list_documents(current_user.id)}


@router.post("/documents/upload")
async def upload_doc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文档"""
    # 校验文件类型
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in ("pdf", "txt", "md", "docx"):
        raise HTTPException(status_code=400, detail="仅支持 PDF、TXT、MD、DOCX 格式")

    # 校验文件大小
    content = await file.read()
    max_bytes = kb_settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {kb_settings.MAX_FILE_SIZE_MB}MB")

    doc_id = upload_and_process(current_user.id, content, file.filename)
    if doc_id is None:
        raise HTTPException(status_code=400, detail=f"上传失败（已达到上限 {kb_settings.MAX_DOCUMENTS_PER_USER} 份或文件无法解析）")

    return {"success": True, "message": "文档上传成功，正在处理中", "data": {"id": doc_id}}


@router.delete("/documents/{doc_id}")
async def delete_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文档"""
    ok = delete_document(current_user.id, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "文档已删除"}
