"""知识库文档服务：上传、解析、分块、向量化、存储"""
import asyncio
import os
import re

import chromadb
import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.knowledge_base import get_kb_settings
from config.database import SessionLocal
from models.knowledge_base import KnowledgeDocument

kb_settings = get_kb_settings()

_chroma_path = os.path.abspath(kb_settings.CHROMA_PERSIST_DIR)
os.makedirs(_chroma_path, exist_ok=True)
_chroma_client = chromadb.PersistentClient(path=_chroma_path)


class DashScopeEmbedding:
    def __init__(self):
        self.api_key = kb_settings.EMBEDDING_API_KEY
        self.base_url = kb_settings.EMBEDDING_BASE_URL.rstrip("/")
        self.model = kb_settings.EMBEDDING_MODEL

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            json={"model": self.model, "input": texts},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )
        data = resp.json()
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API error: {data}")
        items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in items]


embeddings = DashScopeEmbedding()


def _get_collection(user_id: int):
    return _chroma_client.get_or_create_collection(name=f"user_{user_id}_kb")


def _parse_file(file_data: bytes, filename: str) -> str | None:
    """解析文件内容，返回纯文本（仅支持 Markdown）"""
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".md", ".txt"):
        return file_data.decode("utf-8", errors="replace")
    return None


def upload_and_process(user_id: int, file_data: bytes, filename: str) -> int | None:
    """上传并处理文档，返回 document_id"""
    db = SessionLocal()
    try:
        count = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).count()
        if count >= kb_settings.MAX_DOCUMENTS_PER_USER:
            return None
    finally:
        db.close()

    text = _parse_file(file_data, filename)
    if not text:
        return None

    file_type = os.path.splitext(filename)[1].lower().lstrip(".")
    file_size = len(file_data)

    db = SessionLocal()
    try:
        doc = KnowledgeDocument(
            user_id=user_id,
            title=filename,
            file_type=file_type,
            file_size=file_size,
            chunk_count=0,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
    finally:
        db.close()

    asyncio.create_task(_process_document(doc_id, text, user_id))
    return doc_id


def _split_markdown_semantic(text: str, max_chunk: int = 800, overlap: int = 100) -> list[str]:
    """按 Markdown 标题语义分块，保持上下文连贯性"""
    # 按 H2 拆分
    h2_sections = re.split(r"\n(?=## )", text)

    # 提取文档级标题（第一个 # 标题，作为全局上下文）
    doc_title = ""
    first_line = h2_sections[0].strip() if h2_sections else ""
    h1_match = re.match(r"^#\s+[^#]", first_line)
    if h1_match:
        doc_title = first_line.split("\n")[0].strip()
        h2_sections = h2_sections[1:] if len(h2_sections) > 1 else h2_sections

    chunks: list[str] = []
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk, chunk_overlap=overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    for section in h2_sections:
        section = section.strip()
        if not section:
            continue

        # 提取 H2 标题
        h2_title = ""
        lines = section.split("\n")
        if lines and lines[0].startswith("## "):
            h2_title = lines[0].strip()

        # 如果 section 本身很短，直接作为一个 chunk
        if len(section) <= max_chunk:
            prefix = f"{doc_title}\n" if doc_title else ""
            chunks.append(f"{prefix}{section}")
            continue

        # 长 section：按 H3 细分
        sub_parts = re.split(r"\n(?=### )", section)
        for part in sub_parts:
            part = part.strip()
            if not part:
                continue

            if len(part) <= max_chunk:
                prefix = f"{doc_title}\n" if doc_title else ""
                chunks.append(f"{prefix}{part}")
            else:
                # 仍然过长，用 RecursiveCharacterTextSplitter 兜底
                prefix = f"{doc_title}\n" if doc_title else ""
                sub_chunks = fallback_splitter.split_text(part)
                for sc in sub_chunks:
                    chunks.append(f"{prefix}{sc}")

    # 合并相邻短 chunk（避免碎片化）
    merged: list[str] = []
    for ch in chunks:
        if merged and len(merged[-1]) + len(ch) < max_chunk * 0.7:
            merged[-1] = merged[-1] + "\n\n" + ch
        else:
            merged.append(ch)

    return merged if merged else [text[:max_chunk]]


async def _process_document(doc_id: int, text: str, user_id: int):
    """后台处理：分块、向量化、存储"""
    db = SessionLocal()
    try:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            return

        try:
            chunks = _split_markdown_semantic(
                text,
                max_chunk=kb_settings.CHUNK_SIZE,
                overlap=kb_settings.CHUNK_OVERLAP,
            )

            if not chunks:
                doc.status = "completed"
                doc.chunk_count = 0
                db.commit()
                return

            collection = _get_collection(user_id)
            chunk_metas = []
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_metas.append({"document_id": str(doc_id), "title": doc.title})
                chunk_ids.append(f"doc_{doc_id}_chunk_{i}")

            # 批量向量化（API 限制每次最多 10 条）
            all_embeddings = []
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                all_embeddings.extend(embeddings.embed_documents(batch))

            collection.add(
                embeddings=all_embeddings,
                documents=chunks,
                metadatas=chunk_metas,
                ids=chunk_ids,
            )

            doc.status = "completed"
            doc.chunk_count = len(chunks)
            db.commit()
            from services.knowledge_base.retrieval_service import invalidate_rag_cache
            invalidate_rag_cache(user_id)
        except Exception as e:
            doc.status = "failed"
            db.commit()
            print(f"[KB] Process error: {e}")
    finally:
        db.close()


def delete_document(user_id: int, doc_id: int) -> bool:
    """删除文档（DB + ChromaDB）"""
    db = SessionLocal()
    try:
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.user_id == user_id,
        ).first()
        if not doc:
            return False

        try:
            collection = _get_collection(user_id)
            chunk_ids = [f"doc_{doc_id}_chunk_{i}" for i in range(doc.chunk_count + 10)]
            collection.delete(ids=chunk_ids)
        except Exception:
            pass

        db.delete(doc)
        db.commit()
        from services.knowledge_base.retrieval_service import invalidate_rag_cache
        invalidate_rag_cache(user_id)
        return True
    finally:
        db.close()


def list_documents(user_id: int) -> list[dict]:
    """列出用户的所有文档"""
    db = SessionLocal()
    try:
        docs = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).order_by(KnowledgeDocument.create_at.desc()).all()
        return [
            {
                "id": d.id,
                "title": d.title,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "created_at": d.create_at.isoformat() if d.create_at else None,
            }
            for d in docs
        ]
    finally:
        db.close()


def get_document_count(user_id: int) -> int:
    """获取用户文档数量"""
    db = SessionLocal()
    try:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.status == "completed",
        ).count()
    finally:
        db.close()
