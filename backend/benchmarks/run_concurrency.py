"""
AceResearch 检索并发对照：串行 vs 并行（第 2 周 asyncio 证据）

运行：
    cd backend
    python -m backend.benchmarks.run_concurrency

测什么：
    同一组 N 条搜索 query，分别串行（for 循环）和并行（asyncio.gather + Semaphore）执行，
    记录总耗时，得到加速比。证明"并行替代串行"确实生效。

前置：
    1. backend/.env 已配置 TAVILY_API_KEY
    2. 不依赖 MySQL / Redis / DeepSeek（只打 Tavily）
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_here = Path(__file__).parent
_backend = _here.parent
sys.path.insert(0, str(_backend))
os.chdir(str(_backend))

from agents.research.nodes.researcher import _search_one  # noqa: E402

QUERIES = [
    "大语言模型 RAG 检索增强生成",
    "新能源汽车固态电池进展",
    "量子计算纠错最新突破",
    "6G 通信关键技术",
    "可控核聚变商业化",
]


def _mk(q: str, i: int) -> dict:
    return {"id": f"q{i}", "title": q, "description": q, "status": "pending"}


async def _serial(queries: list[str]) -> float:
    t0 = time.perf_counter()
    for i, q in enumerate(queries):
        await _search_one(_mk(q, i))
    return (time.perf_counter() - t0) * 1000.0


async def _parallel(queries: list[str]) -> tuple[float, list[float]]:
    t0 = time.perf_counter()
    latencies: list[float] = []

    async def one(i: int, q: str) -> None:
        s = time.perf_counter()
        await _search_one(_mk(q, i))
        latencies.append((time.perf_counter() - s) * 1000.0)

    await asyncio.gather(*(one(i, q) for i, q in enumerate(queries)))
    return (time.perf_counter() - t0) * 1000.0, latencies


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


async def main() -> None:
    ap = argparse.ArgumentParser(description="检索串行/并行对照")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", type=str, default=str(_here / "concurrency.json"))
    args = ap.parse_args()

    print(f"查询数: {len(QUERIES)} | 重复: {args.repeats} 轮\n")
    serials, parallels = [], []
    for r in range(1, args.repeats + 1):
        s = await _serial(QUERIES)
        p, lats = await _parallel(QUERIES)
        serials.append(s)
        parallels.append(p)
        print(f"  第 {r} 轮  串行 {s/1000:.1f}s   并行 {p/1000:.1f}s   单路最大 {max(lats)/1000:.1f}s")

    s_avg = sum(serials) / len(serials)
    p_avg = sum(parallels) / len(parallels)
    speedup = s_avg / p_avg if p_avg else None

    summary = {
        "meta": {"generated_at": datetime.now(timezone.utc).isoformat(), "queries": len(QUERIES), "repeats": args.repeats},
        "serial_ms": {"avg": round(s_avg, 1), "samples": [round(x, 1) for x in serials]},
        "parallel_ms": {"avg": round(p_avg, 1), "samples": [round(x, 1) for x in parallels]},
        "speedup": round(speedup, 2) if speedup else None,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"串行平均: {s_avg/1000:.1f}s   并行平均: {p_avg/1000:.1f}s")
    print(f"加速比: {speedup:.2f}×  (理论上限 ~{len(QUERIES)}×)")
    print(f"结果已保存: {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
