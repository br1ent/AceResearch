"""
AceResearch 研究流水线基线评测（进程内，第 0 步「量基线」）

运行：
    cd backend
    python -m backend.benchmarks.run_baseline --runs 3      # 冒烟
    python -m backend.benchmarks.run_baseline --runs 20     # 正式基线

采集指标：
    - 端到端时延 P50/P95（从提交主题到报告完成 + 自动总结）
    - 每节点时延 P50/P95（planner / researcher / analyst / writer / reviewer / summarizer）
    - 每份报告 token（按节点累计 input / output / total）
    - Reviewer 打回率（触发重写次数 / 报告数）

前置：
    1. backend/.env 已配置 TAVILY_API_KEY、DB 连接
    2. MySQL 已启动且已导入 agent_prompt.sql（提示词在库里）
    3. 账号 brent@qq.com 已在库中且配置了 DeepSeek API Key

不依赖 FastAPI 服务 / Redis（研究流水线走 Tavily，不走 RAG 缓存）。
执行顺序与 services/research/service.py::_run_execution 保持一致。
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
os.chdir(str(_backend))  # 让 config 读取 backend/.env，ChromaDB 落位 backend/chroma_data

from config.agents import get_agent_settings  # noqa: E402
from config.database import SessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from utils import telemetry  # noqa: E402
from utils.user_llm import get_effective_keys  # noqa: E402

from agents.research.graph import PlanningWorkflow  # noqa: E402
from agents.research.nodes.researcher import researcher_node  # noqa: E402
from agents.research.nodes.analyst import analyst_node  # noqa: E402
from agents.research.nodes.writer import writer_node  # noqa: E402
from agents.research.nodes.reviewer import reviewer_node  # noqa: E402
from services.research.summarizer import summarize_report  # noqa: E402

EMAIL = "brent@qq.com"

TOPICS = [
    "人工智能在医疗诊断中的应用与挑战",
    "全球气候变化对农业的影响及应对策略",
    "区块链技术在供应链管理中的应用",
    "量子计算的发展现状与未来趋势",
    "新能源汽车技术路线对比分析",
    "大语言模型的推理能力与局限性",
    "中国新能源汽车出海面临的挑战",
    "RAG 检索增强生成的技术演进",
    "自动驾驶 L4 的落地难点",
    "可控核聚变的最新进展",
    "低空经济的产业现状与政策",
    "多模态大模型的架构对比",
    "边缘计算与端侧 AI 部署",
    "AIGC 对内容创作行业的影响",
    "6G 通信的关键技术方向",
    "脑机接口的研究进展与伦理",
    "具身智能机器人的发展瓶颈",
    "向量数据库的选型与优化",
    "端侧大模型的量化与蒸馏",
    "数据要素市场的现状与问题",
]


def percentile(values: list[float], p: float) -> float | None:
    """线性插值分位数，空列表返回 None。"""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def get_user_id() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == EMAIL).first()
    finally:
        db.close()
    if not user:
        raise SystemExit(f"账号 {EMAIL} 不存在，请确认已注册")
    deepseek_key, _, _ = get_effective_keys(user.id)
    if not deepseek_key:
        raise SystemExit(f"账号 {EMAIL} 未配置 DeepSeek API Key，无法运行基准")
    return user.id


async def run_one(planning: PlanningWorkflow, user_id: int, topic: str) -> dict:
    """跑一次完整研究流水线，返回本次运行记录。"""
    telemetry.reset()

    state = await planning.run(topic, user_id, 0)
    state.update({"status": "running", "progress": 25.0})

    # 与 _run_execution 相同的节点执行顺序
    state.update(await researcher_node(state))
    state.update(await analyst_node(state))
    state.update(await writer_node(state))
    state.update(await reviewer_node(state))
    if state["status"] != "completed":
        state.update(await writer_node(state))
        state.update(await reviewer_node(state))

    final_report = state.get("final_report") or state.get("report_draft", "")
    rewrites = state.get("reviewer_retries", 0)

    if final_report:
        try:
            await summarize_report(
                title=state.get("report_title", topic),
                outline=state.get("outline", []),
                content=final_report,
                user_id=user_id,
            )
        except Exception:
            pass

    return {
        "topic": topic,
        "status": state.get("status", "unknown"),
        "rewrites": rewrites,
        "records": telemetry.records(),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="研究流水线基线评测")
    parser.add_argument("--runs", type=int, default=20, help="跑几篇（默认 20）")
    parser.add_argument("--out", type=str, default=str(_here / "baseline.json"))
    args = parser.parse_args()

    agent = get_agent_settings()
    user_id = get_user_id()
    topics = [TOPICS[i % len(TOPICS)] for i in range(args.runs)]
    planning = PlanningWorkflow()

    print(f"模型: {agent.DEEPSEEK_MODEL} | 账号: {EMAIL} (id={user_id}) | 篇数: {args.runs}\n")

    telemetry.enable()
    runs: list[dict] = []
    for i, topic in enumerate(topics, 1):
        t0 = time.perf_counter()
        try:
            rec = await run_one(planning, user_id, topic)
        except Exception as e:
            print(f"  [{i:2d}] {topic[:28]:<30} ✗ 失败: {type(e).__name__}: {e}")
            runs.append({
                "topic": topic, "status": "error", "rewrites": 0, "error": str(e),
                "elapsed_ms": (time.perf_counter() - t0) * 1000.0, "records": telemetry.records(),
            })
            continue
        rec["elapsed_ms"] = (time.perf_counter() - t0) * 1000.0
        runs.append(rec)
        print(f"  [{i:2d}] {topic[:28]:<30} {rec['status']:<10} 重写{rec['rewrites']}次  端到端 {rec['elapsed_ms']/1000:.1f}s")
    telemetry.disable()

    ok = [r for r in runs if r["status"] == "completed"]
    e2e = [r["elapsed_ms"] for r in ok]
    rewrites_total = sum(r["rewrites"] for r in ok)

    # 每节点时延 / token 聚合
    node_lat: dict[str, list[float]] = {}
    node_tokens: dict[str, dict[str, list[int]]] = {}
    for r in runs:
        for rec in r["records"]:
            n = rec.get("node", "?")
            lat = rec.get("latency_ms")
            if lat is not None:
                node_lat.setdefault(n, []).append(lat)
            tok = rec.get("tokens")
            if tok:
                for k, v in tok.items():
                    node_tokens.setdefault(n, {}).setdefault(k, []).append(v)

    per_report_tokens = []
    for r in ok:
        total_in = total_out = 0
        for rec in r["records"]:
            tok = rec.get("tokens")
            if tok:
                total_in += tok.get("input_tokens", 0)
                total_out += tok.get("output_tokens", 0)
        per_report_tokens.append({"topic": r["topic"], "input": total_in, "output": total_out, "total": total_in + total_out})

    summary = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": agent.DEEPSEEK_MODEL,
            "user_email": EMAIL,
            "runs": args.runs,
            "completed": len(ok),
            "failed": len(runs) - len(ok),
        },
        "end_to_end_ms": {
            "p50": round(percentile(e2e, 0.50) or 0, 1),
            "p95": round(percentile(e2e, 0.95) or 0, 1),
            "avg": round(sum(e2e) / len(e2e), 1) if e2e else None,
            "samples": [round(x, 1) for x in e2e],
        },
        "per_node_ms": {
            n: {
                "p50": round(percentile(v, 0.50) or 0, 1),
                "p95": round(percentile(v, 0.95) or 0, 1),
                "avg": round(sum(v) / len(v), 1),
                "count": len(v),
            }
            for n, v in node_lat.items()
        },
        "tokens": {
            "per_report_avg": {
                "input": round(sum(t["input"] for t in per_report_tokens) / len(per_report_tokens), 1) if per_report_tokens else None,
                "output": round(sum(t["output"] for t in per_report_tokens) / len(per_report_tokens), 1) if per_report_tokens else None,
                "total": round(sum(t["total"] for t in per_report_tokens) / len(per_report_tokens), 1) if per_report_tokens else None,
            },
            "by_node": {
                n: {k: round(sum(v) / len(v), 1) for k, v in d.items()}
                for n, d in node_tokens.items()
            },
        },
        "rewrite": {
            "rate": round(rewrites_total / len(ok), 4) if ok else None,
            "rewrites": rewrites_total,
            "reports": len(ok),
        },
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("                        基线结果")
    print("=" * 70)
    e2e_s = summary["end_to_end_ms"]
    rw = summary["rewrite"]
    tk = summary["tokens"]["per_report_avg"]
    print(f"端到端: P50 {e2e_s['p50']/1000:.1f}s  P95 {e2e_s['p95']/1000:.1f}s  平均 {e2e_s['avg']/1000:.1f}s")
    print(f"打回率: {(rw['rate'] or 0)*100:.1f}%  (重写 {rw['rewrites']} 次 / {rw['reports']} 篇)")
    print(f"每报告 token: 平均 total={tk['total']}  (input={tk['input']} / output={tk['output']})")

    print("\n| 节点 | P50(ms) | P95(ms) | 平均(ms) | 次数 |")
    print("|------|---------|---------|----------|------|")
    for n, v in sorted(node_lat.items(), key=lambda kv: -(sum(kv[1]) / len(kv[1]) if kv[1] else 0)):
        print(f"| {n} | {percentile(v, 0.50):.0f} | {percentile(v, 0.95):.0f} | {sum(v)/len(v):.0f} | {len(v)} |")

    print(f"\n结果已保存: {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
