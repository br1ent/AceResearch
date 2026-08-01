"""
AceResearch 质量评测脚本
  1. RAG 检索准确率评测 — 30 条查询
  2. 报告重写率评测 — 7 篇报告

运行方式（项目根目录）：
    python -m backend.tests.ace_eval_full

依赖：httpx, asyncio（标准库）
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

# ─── 配置 ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "eval_full@qq.com"
TEST_PASSWORD = "123456"
TOP_K = 3

# 30 条 RAG 查询（与现有 ace_research_eval.py 的 60 条不重复）
RAG_QUERIES = [
    # 通用技术
    ("微服务间用什么通信协议", "HTTP"),
    ("注册中心用的是哪个组件", "Nacos"),
    ("数据库主从同步用什么方式", "binlog"),
    ("Redis 缓存用的什么淘汰策略", "lru"),
    ("消息队列用的哪个中间件", "RabbitMQ"),
    ("搜索服务用的什么框架", "Elasticsearch"),
    ("文件上传服务用的什么 OSS", "OSS"),
    ("限流算法用的是哪一种", "令牌桶"),
    ("分布式锁用的什么实现", "Redisson"),
    ("链路追踪用的什么方案", "SkyWalking"),
    # 前端技术
    ("Vue 组件通信用什么方式传递父到子", "props"),
    ("Pinia 状态管理的核心概念是什么", "store"),
    ("Vue Router 导航守卫怎么配置", "beforeEach"),
    ("Axios 请求拦截器在哪里定义", "interceptors"),
    # 后端技术
    ("MyBatis Plus 怎么实现分页查询", "Page"),
    ("Spring Boot starter 依赖由谁管理", "parent"),
    ("FastAPI 路径参数怎么定义", "path"),
    ("SQLAlchemy 的 Session 由谁管理", "SessionLocal"),
    ("Pydantic 的 BaseModel 用来做什么", "validation"),
    ("异步任务用的什么队列", "Celery"),
    # 数据库与中间件
    ("MongoDB 的文档_id 默认是什么类型", "ObjectId"),
    ("Kafka 的分区副本同步机制是什么", "ISR"),
    ("ClickHouse 用于什么场景", "OLAP"),
    ("ShardingSphere 用的是什么分片策略", "mod"),
    # 项目架构
    ("前端工程化用的什么构建工具", "Vite"),
    ("后端接口文档用的什么框架", "Swagger"),
    ("Git Flow 分支策略有哪些分支", "develop"),
    ("Docker 镜像基于什么操作系统", "Alpine"),
    ("K8s 集群最小节点数是多少", "master"),
    ("CI/CD 用的是什么流水线工具", "Jenkins"),
]

# 7 个研究报告主题（多样化，覆盖不同领域）
REPORT_TOPICS = [
    "人工智能在医疗诊断中的应用与挑战",
    "全球气候变化对农业的影响及应对策略",
    "区块链技术在供应链管理中的应用",
    "量子计算的发展现状与未来趋势",
    "远程办公对企业管理的影响研究",
    "新能源汽车技术路线对比分析",
    "短视频平台对青少年心理健康的影响",
]


# ════════════════════════════════════════════════════════════════════════════
# 第一部分：RAG 检索准确率评测
# ════════════════════════════════════════════════════════════════════════════

async def eval_rag(client: httpx.AsyncClient, token: str, user_id: int) -> dict:
    """评测 RAG 检索准确率"""
    from services.knowledge_base.retrieval_service import search_knowledge

    print(f"\n{'='*60}")
    print("  第一部分：RAG 检索准确率评测")
    print('='*60)
    print(f"查询数量: {len(RAG_QUERIES)} 条 | TOP_K: {TOP_K}\n")

    recalls: list[int] = []
    mrrs: list[float] = []
    hit_details: list[dict] = []

    print(f"{'#':>3}  {'查询':<40} {'关键词':<16} {'结果'}")
    print("-" * 75)

    for i, (query, keyword) in enumerate(RAG_QUERIES, 1):
        raw = search_knowledge(user_id, query, top_k=TOP_K)
        hit = keyword.lower() in raw.lower()

        mrr = 0.0
        if hit:
            sources = raw.lower().split("[来源")
            for rank, src in enumerate(sources[1:], 1):
                if keyword.lower() in src:
                    mrr = 1.0 / rank
                    break

        recalls.append(1 if hit else 0)
        mrrs.append(mrr)
        hit_details.append({"query": query, "keyword": keyword, "hit": hit, "mrr": mrr})

        mark = "✓" if hit else "✗"
        print(f"  {i:>3}  {query[:38]:<40} {keyword:<16} {mark}  MRR={mrr:.2f}")

    recall_score = sum(recalls) / len(recalls) * 100
    mrr_score = sum(mrrs) / len(mrrs) * 100
    hit_count = sum(recalls)

    print(f"\n{'='*60}")
    print("  RAG 评测结果")
    print('='*60)
    print(f"  查询数量:      {len(RAG_QUERIES)}")
    print(f"  命中数量:      {hit_count} / {len(RAG_QUERIES)}")
    print(f"  Recall@{TOP_K}:     {recall_score:.1f}%")
    print(f"  MRR@{TOP_K}:        {mrr_score:.1f}%")
    print('='*60)

    return {
        "total_queries": len(RAG_QUERIES),
        "hit_count": hit_count,
        f"recall@{TOP_K}": round(recall_score, 1),
        f"mrr@{TOP_K}": round(mrr_score, 1),
        "details": hit_details,
    }


# ════════════════════════════════════════════════════════════════════════════
# 第二部分：报告重写率评测
# ════════════════════════════════════════════════════════════════════════════

async def _wait_for_report_completed(
    client: httpx.AsyncClient,
    headers: dict,
    conversation_id: int,
    timeout: int = 300,
    poll_interval: int = 5,
) -> dict | None:
    """轮询等待报告完成，返回包含 reviewer_rewrite_count 的报告数据或 None（超时）"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(poll_interval)
        r = await client.get(
            f"{BASE_URL}/api/chat/conversations/{conversation_id}/report",
            headers=headers,
            timeout=10.0,
        )
        if r.status_code == 200:
            data = r.json().get("data")
            if data and data.get("status") in ("completed", "failed"):
                # 获取 reviewer_rewrite_count（/api/reports/ 有完整字段）
                reports_r = await client.get(
                    f"{BASE_URL}/api/reports/",
                    headers=headers,
                    timeout=10.0,
                )
                if reports_r.status_code == 200:
                    reports_list = reports_r.json().get("data", [])
                    for rep in reports_list:
                        # 跳过 planning/generating 状态的旧报告，找已完成/失败且最新的
                        if rep.get("status") in ("completed", "failed"):
                            return rep
                return data  # 回退：返回已有数据
    return None


async def eval_report_rewrite(
    client: httpx.AsyncClient,
    headers: dict,
    user_id: int,
) -> dict:
    """评测报告重写率：生成 7 篇报告，统计 reviewer 触发重写的比例"""
    print(f"\n{'='*60}")
    print("  第二部分：报告重写率评测")
    print('='*60)
    print(f"报告数量: {len(REPORT_TOPICS)} 篇\n")
    print(f"{'#':>3}  {'主题':<46} {'状态':<14} {'重写次数':<8} {'耗时(s)'}")
    print("-" * 85)

    report_results: list[dict] = []
    rewrite_count_total = 0
    completed_count = 0
    failed_count = 0

    for i, topic in enumerate(REPORT_TOPICS, 1):
        t0 = time.time()

        # 1. 创建对话
        r_conv = await client.post(
            f"{BASE_URL}/api/chat/conversations",
            json={"title": topic[:30], "mode": "research"},
            headers=headers,
            timeout=15.0,
        )
        if r_conv.status_code != 200:
            print(f"  {i:>3}  {topic[:44]:<46} [错误] 创建对话失败")
            report_results.append({"topic": topic, "status": "error", "rewrite_count": 0, "elapsed": 0})
            continue
        conv_id = r_conv.json()["data"]["id"]

        # 2. 启动研究
        r_start = await client.post(
            f"{BASE_URL}/api/chat/send",
            json={"conversation_id": conv_id, "message": topic, "mode": "research"},
            headers=headers,
            timeout=30.0,
        )
        if r_start.status_code != 200:
            print(f"  {i:>3}  {topic[:44]:<46} [错误] 启动研究失败")
            report_results.append({"topic": topic, "status": "error", "rewrite_count": 0, "elapsed": 0})
            continue

        # 3. 轮询直到报告完成
        report_data = await _wait_for_report_completed(client, headers, conv_id, timeout=300)
        elapsed = time.time() - t0

        if report_data is None:
            print(f"  {i:>3}  {topic[:44]:<46} [超时]")
            report_results.append({"topic": topic, "status": "timeout", "rewrite_count": 0, "elapsed": elapsed})
            continue

        status = report_data.get("status", "unknown")
        rewrite_cnt = report_data.get("reviewer_rewrite_count", 0)
        rewrite_count_total += rewrite_cnt

        if status == "completed":
            completed_count += 1
        else:
            failed_count += 1

        report_results.append({
            "topic": topic,
            "status": status,
            "rewrite_count": rewrite_cnt,
            "elapsed": round(elapsed, 1),
        })

        status_display = {
            "completed": "✓ 完成",
            "failed": "✗ 失败",
            "timeout": "○ 超时",
            "generating": "… 生成中",
        }.get(status, status)

        rewrite_display = f"{rewrite_cnt}x" if rewrite_cnt > 0 else "0"
        print(f"  {i:>3}  {topic[:44]:<46} {status_display:<14} {rewrite_display:<8} {elapsed:.1f}s")

    total = len(report_results)
    rewrite_rate = rewrite_count_total / completed_count * 100 if completed_count else 0

    print(f"\n{'='*60}")
    print("  报告评测结果")
    print('='*60)
    print(f"  报告总数:      {total} 篇")
    print(f"  完成数量:      {completed_count} 篇")
    print(f"  失败数量:      {failed_count} 篇")
    print(f"  总重写次数:    {rewrite_count_total}")
    print(f"  重写率:        {rewrite_rate:.1f}%  (重写次数 / 完成报告数)")
    print(f"  平均生成耗时:  ", end="")
    completed_results = [r for r in report_results if r["status"] == "completed"]
    if completed_results:
        avg_elapsed = sum(r["elapsed"] for r in completed_results) / len(completed_results)
        print(f"{avg_elapsed:.1f}s")
    else:
        print("N/A")
    print('='*60)

    return {
        "total_reports": total,
        "completed": completed_count,
        "failed": failed_count,
        "total_rewrite_count": rewrite_count_total,
        "rewrite_rate": round(rewrite_rate, 1),
        "avg_elapsed": round(
            sum(r["elapsed"] for r in completed_results) / len(completed_results), 1
        ) if completed_results else None,
        "details": report_results,
    }


# ════════════════════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════════════════════

async def main():
    print(f"\n{'='*60}")
    print("  AceResearch 完整质量评测")
    print('='*60)
    print(f"目标服务: {BASE_URL}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # ── 登录 / 注册 ──────────────────────────────────────────────
        login_resp = await client.post(
            f"{BASE_URL}/api/user/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if login_resp.status_code == 200 and login_resp.json().get("success"):
            print(f"[账号] 登录成功: {TEST_EMAIL}")
            token = login_resp.json()["data"]["access_token"]
            user_id = int(login_resp.json()["data"]["user"]["id"])
        else:
            print(f"[账号] 账号不存在，正在注册...")
            reg_resp = await client.post(
                f"{BASE_URL}/api/user/register",
                json={
                    "username": "eval_full_user",
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "confirm_password": TEST_PASSWORD,
                },
            )
            if reg_resp.status_code == 200:
                login_resp2 = await client.post(
                    f"{BASE_URL}/api/user/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                )
                token = login_resp2.json()["data"]["access_token"]
                user_id = int(login_resp2.json()["data"]["user"]["id"])
                print(f"[账号] 注册并登录成功: {TEST_EMAIL}")
            else:
                print(f"[账号] 登录失败: {login_resp.text}")
                return

        headers = {"Authorization": f"Bearer {token}"}

        # ── 等待文档处理完毕 ─────────────────────────────────────────
        print("\n[知识库] 等待文档处理完毕...")
        docs_ready = False
        doc_names: list[str] = []
        for attempt in range(12):
            await asyncio.sleep(5)
            r_list = await client.get(f"{BASE_URL}/api/kb/documents", headers=headers)
            if r_list.status_code == 200:
                docs = r_list.json().get("data", [])
                completed = [d for d in docs if d.get("status") == "completed"]
                if completed:
                    doc_names = [d.get("title", "?") for d in completed]
                    print(f"[知识库] {len(completed)} 篇文档处理完毕")
                    docs_ready = True
                    break
                print(f"[知识库] 第 {attempt+1} 次轮询，文档仍在处理中...")

        if not docs_ready:
            print("[警告] 文档未处理完毕，将使用当前可用文档继续评测\n")
            r_list = await client.get(f"{BASE_URL}/api/kb/documents", headers=headers)
            if r_list.status_code == 200:
                docs = r_list.json().get("data", [])
                doc_names = [d.get("title", "?") for d in docs if d.get("status") == "completed"]

        # ── 第一部分：RAG 评测 ────────────────────────────────────────
        rag_result = await eval_rag(client, token, user_id)

        # ── 第二部分：报告重写率评测 ─────────────────────────────────
        # 清理旧对话避免干扰
        r_list = await client.get(f"{BASE_URL}/api/chat/conversations", headers=headers)
        if r_list.status_code == 200:
            for conv in r_list.json().get("data", []):
                cid = conv.get("id")
                if cid:
                    await client.delete(
                        f"{BASE_URL}/api/chat/conversations/{cid}",
                        headers=headers,
                        timeout=10.0,
                    )

        report_result = await eval_report_rewrite(client, headers, user_id)

        # ── 综合输出 ─────────────────────────────────────────────────
        final_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "documents": doc_names,
            "rag": rag_result,
            "report_rewrite": report_result,
        }

        out_path = os.path.join(os.path.dirname(__file__), "eval_full_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)

        print(f"\n[结果] 评测完成，已保存: {out_path}")
        print("\n综合结果:")
        print(f"  RAG Recall@{TOP_K}:       {rag_result[f'recall@{TOP_K}']}%")
        print(f"  RAG MRR@{TOP_K}:          {rag_result[f'mrr@{TOP_K}']}%")
        print(f"  报告重写率:               {report_result['rewrite_rate']}%  ({report_result['total_rewrite_count']} 次 / {report_result['completed']} 篇)")


if __name__ == "__main__":
    asyncio.run(main())
