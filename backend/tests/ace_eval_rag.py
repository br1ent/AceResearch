"""
RAG 知识库检索准确率评估脚本（AceResearch 版）

使用方法：
    cd backend
    python tests/ace_eval_rag.py
    # 或从项目根目录
    python -m backend.tests.ace_eval_rag

流程：
    1. ChromaDB 向量召回 10 个候选文档（百炼 text-embedding-v4）
    2. Rerank 重排序后取 top-3（qwen3-rerank）
    3. 在 top-3 上计算指标

评估指标：
    - Recall@3: top-3 结果中关键词覆盖率（命中的关键词数 / 总关键词数）
    - Precision@3: top-3 结果中相关文档的占比
    - MRR (Mean Reciprocal Rank): 第一个相关文档的平均倒数排名
    - Hit Rate: 至少命中一个相关文档的查询比例

测试集 test_queries.json：41 条查询，按 architecture / auth / model / agent / rag / cache / frontend
共 7 大知识维度组织，单条可含多个相关关键词以检验语义召回与多文档整合能力。

前置条件：
    1. 被评测用户已上传并处理完知识库文档（test_queries.json 面向 test_doc.md 设计）
    2. backend/.env 已配置 EMBEDDING_API_KEY / RERANK_WORKSPACE_ID / RERANK_MODEL
    3. 通过环境变量 RAG_EVAL_USER_ID 指定被评测用户（默认 8，即存放 test_doc.md 的账号）
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# 路径处理（支持直接运行和 python -m 两种方式）
_tests_dir = Path(__file__).parent
backend_dir = _tests_dir.parent  # AceResearch/backend
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))  # 使 config 能读取 backend/.env，ChromaDB 落位 backend/chroma_data

import httpx
from config.knowledge_base import get_kb_settings
from services.knowledge_base.document_service import _get_collection, embeddings

kb_settings = get_kb_settings()

# 被评测用户（ChromaDB 按 user_{id}_kb 隔离），默认 8 = 存放 test_doc.md 的账号
USER_ID = int(os.getenv("RAG_EVAL_USER_ID", "8"))

RERANK_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"


@dataclass
class QueryResult:
    """单个查询的评测结果"""
    query: str
    hit: bool
    recall_at_3: float
    precision_at_3: float
    mrr: float
    top_titles: List[str]


class RAGEvaluator:
    VECTOR_RECALL_K = 10    # 向量召回 10 个候选
    FINAL_TOP_K = 3         # Rerank 后取 top-3

    def __init__(self):
        self.collection = _get_collection(USER_ID)

    def _rerank(self, query: str, documents: list[str]) -> list[dict] | None:
        """调用 qwen3-rerank 对候选文本重排序，返回按相关性降序的结果"""
        if not kb_settings.RERANK_WORKSPACE_ID or not documents:
            return None
        try:
            resp = httpx.post(
                RERANK_URL,
                json={
                    "model": kb_settings.RERANK_MODEL,
                    "input": {
                        "query": query,
                        "documents": documents,
                    },
                    "parameters": {
                        "top_n": self.FINAL_TOP_K,
                        "return_documents": True,
                    },
                },
                headers={"Authorization": f"Bearer {kb_settings.EMBEDDING_API_KEY}"},
                timeout=30.0,
            )
            if resp.status_code == 200:
                results = resp.json().get("output", {}).get("results", [])
                return sorted(results, key=lambda r: r.get("relevance_score", 0), reverse=True)
        except Exception as e:
            print(f"[Rerank] ERROR: {e}")

        return None

    def _is_relevant(self, doc_text: str, keywords: list[str]) -> bool:
        """判断文档是否与关键词相关（大小写不敏感的子串匹配）"""
        for kw in keywords:
            if kw.lower() in doc_text.lower():
                return True
        return False

    def _compute_metrics(self, query: str, doc_texts: list[str],
                         doc_metas: list[dict], keywords: list[str]) -> QueryResult:
        """对 top-k 文档计算指标"""
        # Recall: 关键词覆盖率
        covered = set()
        for kw in keywords:
            for doc in doc_texts:
                if kw.lower() in doc.lower():
                    covered.add(kw)
                    break
        recall = len(covered) / len(keywords) if keywords else 0

        # Precision: top-3 中命中的比例
        hits = sum(1 for doc in doc_texts if self._is_relevant(doc, keywords))

        # MRR: 第一个命中文档的倒数排名
        mrr = 0.0
        for i, doc in enumerate(doc_texts):
            if self._is_relevant(doc, keywords):
                mrr = 1.0 / (i + 1)
                break

        return QueryResult(
            query=query,
            hit=recall > 0,
            recall_at_3=recall,
            precision_at_3=hits / self.FINAL_TOP_K,
            mrr=mrr,
            top_titles=[m.get("title", "?") for m in doc_metas],
        )

    def evaluate(self, query: str, keywords: list[str]) -> QueryResult:
        """执行检索管线：向量召回 N 个 → Rerank → top-3"""
        # 1. 向量召回
        total = self.collection.count()
        if total == 0:
            raise RuntimeError("知识库为空，请先上传并处理文档")
        recall_k = min(self.VECTOR_RECALL_K, total)
        query_embedding = embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=recall_k,
            include=["documents", "metadatas"],
        )
        doc_texts = results["documents"][0]
        doc_metas = results["metadatas"][0]

        # 2. Rerank 重排序
        ranked = self._rerank(query, doc_texts)
        if ranked:
            final_texts = []
            final_metas = []
            for item in ranked:
                idx = item["index"]
                if idx < len(doc_texts):
                    final_texts.append(doc_texts[idx])
                    final_metas.append(doc_metas[idx])
        else:
            # Rerank 不可用时，直接取向量召回的 top-3
            final_texts = doc_texts[:self.FINAL_TOP_K]
            final_metas = doc_metas[:self.FINAL_TOP_K]

        # 3. 计算指标
        return self._compute_metrics(query, final_texts, final_metas, keywords)

    def run(self, test_file: str):
        with open(test_file, 'r', encoding='utf-8') as f:
            queries = json.load(f)

        print(f"测试集: {len(queries)} 个查询 | 用户: {USER_ID}")
        print(f"管  线: 向量召回 {self.VECTOR_RECALL_K} 个 → Rerank → top-{self.FINAL_TOP_K}")
        print()

        all_results = []

        for i, item in enumerate(queries, 1):
            q = item['query']
            keywords = item['relevant_keywords']
            category = item.get('category', '')
            result = self.evaluate(q, keywords)
            all_results.append((result, category))

            mark = "[OK]" if result.hit else "[NO]"
            head = f"[{category}] {q}" if category else q
            print(f"[{i:2d}] {mark} {head}")
            print(f"     关键词: {', '.join(keywords[:5])}{'…' if len(keywords) > 5 else ''}")
            print(f"     Recall@3={result.recall_at_3:.0%}  Precision@3={result.precision_at_3:.0%}  MRR={result.mrr:.2f}")
            print(f"     top-3: {result.top_titles}")

        # 汇总
        n = len(all_results)
        recall_avg = sum(r.recall_at_3 for r, _ in all_results) / n
        precision_avg = sum(r.precision_at_3 for r, _ in all_results) / n
        mrr_avg = sum(r.mrr for r, _ in all_results) / n
        hit_rate = sum(1 for r, _ in all_results if r.hit) / n

        print()
        print("=" * 60)
        print("                    评测汇总")
        print("=" * 60)
        print(f"{'指标':<20} {'数值':>12} {'达标':>8}")
        print("-" * 60)
        for label, val, threshold in [
            ("Recall@3", recall_avg, 0.85),
            ("Precision@3", precision_avg, None),
            ("MRR", mrr_avg, 0.8),
            ("Hit Rate", hit_rate, 0.90),
        ]:
            ok = val >= threshold if threshold else "—"
            ok_str = "OK" if ok is True else ("FAIL" if ok is False else ok)
            print(f"{label:<20} {val:>11.1%} {ok_str:>8}")
        print("-" * 60)

        # 保存报告
        report = {
            "config": {
                "user_id": USER_ID,
                "vector_recall_k": self.VECTOR_RECALL_K,
                "final_top_k": self.FINAL_TOP_K,
                "test_count": n,
            },
            "summary": {
                "recall_at_3": recall_avg,
                "precision_at_3": precision_avg,
                "mrr": mrr_avg,
                "hit_rate": hit_rate,
            },
            "details": [
                {
                    "query": r.query,
                    "category": cat,
                    "hit": r.hit,
                    "recall_at_3": r.recall_at_3,
                    "precision_at_3": r.precision_at_3,
                    "mrr": r.mrr,
                    "top_titles": r.top_titles,
                }
                for r, cat in all_results
            ],
        }

        report_file = _tests_dir / "rag_evaluation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    test_file = _tests_dir / "test_queries.json"
    if not test_file.exists():
        print(f"测试文件不存在: {test_file}")
        sys.exit(1)

    evaluator = RAGEvaluator()
    evaluator.run(str(test_file))
