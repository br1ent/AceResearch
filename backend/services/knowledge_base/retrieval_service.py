"""知识库检索服务（召回 + 重排序）"""

import httpx
from services.knowledge_base.document_service import _get_collection, embeddings
from config.knowledge_base import get_kb_settings

kb_settings = get_kb_settings()


def _rerank(query: str, documents: list[str]) -> list[dict] | None:
    """调用 qwen3-rerank 对候选文本重排序，返回排序后的结果列表"""
    if not kb_settings.RERANK_WORKSPACE_ID or not documents:
        return None

    url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    try:
        resp = httpx.post(
            url,
            json={
                "model": kb_settings.RERANK_MODEL,
                "input": {
                    "query": query,
                    "documents": documents,
                },
                "parameters": {
                    "top_n": kb_settings.RERANK_TOP_N,
                    "return_documents": True,
                },
            },
            headers={"Authorization": f"Bearer {kb_settings.EMBEDDING_API_KEY}"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("output", {}).get("results", [])
            sorted_results = sorted(results, key=lambda r: r.get("relevance_score", 0), reverse=True)
            return sorted_results
    except Exception as e:
        print(f"[Rerank] ERROR: {e}")

    return None


def search_knowledge(user_id: int, query: str, top_k: int = 5) -> str:
    """搜索知识库（向量召回 + 重排序），返回格式化的文本块"""
    try:
        collection = _get_collection(user_id)
        if collection.count() == 0:
            return "知识库中没有文档内容"

        # 向量召回（固定 10 条候选）
        recall_k = min(collection.count(), kb_settings.RECALL_K)
        query_embedding = embeddings.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=recall_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return "未找到相关内容"

        docs = results["documents"][0]
        metas = results["metadatas"][0]

        # 重排序
        reranked = _rerank(query, docs)
        if reranked:
            lines = []
            for i, item in enumerate(reranked, 1):
                idx = item.get("index", i - 1)
                title = metas[idx].get("title", "未知文档") if idx < len(metas) else "未知文档"
                content = item.get("document", {}).get("text", docs[idx] if idx < len(docs) else "")
                lines.append(f"[来源 {i}] 文档：{title}\n内容：{content}")
            return "\n\n".join(lines)

        # 重排序不可用，用原始向量距离排序（仅返回 top-3）
        lines = []
        for i, (doc, meta) in enumerate(zip(docs[:top_k], metas[:top_k]), 1):
            title = meta.get("title", "未知文档")
            lines.append(f"[来源 {i}] 文档：{title}\n内容：{doc}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"知识库检索失败：{e}"
