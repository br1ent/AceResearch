"""
AceResearch RAG 知识库缓存命中率 + 检索时延评测（第 0 步「量基线」）

运行：
    cd backend
    python -m backend.benchmarks.run_rag_cache

流程：
    对每条 query 跑两遍：第一遍填充缓存（miss），第二遍命中（hit），
    统计缓存命中率 + hit/miss 检索时延 P50/P95。

前置：
    1. 账号已上传至少一份 Markdown 文档到知识库
    2. 账号已配置百炼 embedding key + rerank workspace id
    3. Redis 已启动
    4. backend/tests/test_queries.json 存在（面向该账号文档的查询集；不存在则用内置示例 query）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_here = Path(__file__).parent
_backend = _here.parent
sys.path.insert(0, str(_backend))
os.chdir(str(_backend))

from config.database import SessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from utils import telemetry  # noqa: E402
from utils.user_llm import get_effective_keys  # noqa: E402
from services.knowledge_base.document_service import _get_collection  # noqa: E402
from services.knowledge_base.retrieval_service import (  # noqa: E402
    search_knowledge, get_cache_stats, reset_cache_stats, invalidate_rag_cache,
)

EMAIL = "brent@qq.com"

FALLBACK_QUERIES = [
    "这个项目用了什么架构",
    "认证是怎么实现的",
    "缓存的设计思路是什么",
    "前端用的什么技术栈",
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def get_user_id(email: str) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()
    if not user:
        raise SystemExit(f"账号 {email} 不存在")
    _, dashscope, workspace = get_effective_keys(user.id)
    if not dashscope or not workspace:
        raise SystemExit(f"账号 {email} 未配置百炼 Key / Workspace ID，无法检索")
    return user.id


def load_queries() -> list[str]:
    qf = _backend / "tests" / "test_queries.json"
    if qf.exists():
        with open(qf, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data and "query" in data[0]:
            return [item["query"] for item in data]
    return FALLBACK_QUERIES


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 缓存命中率评测")
    parser.add_argument("--email", type=str, default=EMAIL)
    parser.add_argument("--out", type=str, default=str(_here / "baseline_rag_cache.json"))
    args = parser.parse_args()

    user_id = get_user_id(args.email)
    queries = load_queries()

    collection = _get_collection(user_id)
    if collection.count() == 0:
        raise SystemExit(f"账号 {args.email} 的知识库为空，请先上传文档")

    print(f"账号: {args.email} (id={user_id}) | 文档块: {collection.count()} | 查询: {len(queries)}\n")

    telemetry.enable()
    reset_cache_stats(user_id)
    invalidate_rag_cache(user_id)

    # 第一遍：全部 miss（填充缓存）
    for q in queries:
        search_knowledge(user_id, q)
    # 第二遍：全部 hit
    for q in queries:
        search_knowledge(user_id, q)
    telemetry.disable()

    stats = get_cache_stats(user_id)
    recs = telemetry.records()
    hit_lat = [r["latency_ms"] for r in recs if r.get("cache") == "hit" and r.get("latency_ms") is not None]
    miss_lat = [r["latency_ms"] for r in recs if r.get("cache") == "miss" and r.get("latency_ms") is not None]

    summary = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user_email": args.email,
            "queries": len(queries),
        },
        "cache": stats,
        "latency_ms": {
            "hit": {
                "p50": round(percentile(hit_lat, 0.50) or 0, 1),
                "p95": round(percentile(hit_lat, 0.95) or 0, 1),
                "avg": round(sum(hit_lat) / len(hit_lat), 1) if hit_lat else None,
                "count": len(hit_lat),
            },
            "miss": {
                "p50": round(percentile(miss_lat, 0.50) or 0, 1),
                "p95": round(percentile(miss_lat, 0.95) or 0, 1),
                "avg": round(sum(miss_lat) / len(miss_lat), 1) if miss_lat else None,
                "count": len(miss_lat),
            },
        },
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("                  RAG 缓存基线")
    print("=" * 60)
    print(f"命中率: {stats.get('hit_rate') and stats['hit_rate']*100:.1f}%  (hit={stats['hits']} miss={stats['misses']})")
    h, m = summary["latency_ms"]["hit"], summary["latency_ms"]["miss"]
    print(f"命中时延: P50 {h['p50']:.1f}ms  P95 {h['p95']:.1f}ms  平均 {h['avg']:.1f}ms")
    print(f"未命中时延: P50 {m['p50']:.1f}ms  P95 {m['p95']:.1f}ms  平均 {m['avg']:.1f}ms")
    if h["avg"] and m["avg"] and m["avg"] > 0:
        print(f"加速比: 命中 / 未命中 ≈ {m['avg']/h['avg']:.1f}x")
    print(f"\n结果已保存: {args.out}")


if __name__ == "__main__":
    main()
