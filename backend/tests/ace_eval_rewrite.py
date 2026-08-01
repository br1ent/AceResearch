"""
AceResearch 报告重写率评测（5 篇，自动确认方案）

运行:
    cd AceResearch/backend
    python -m backend.tests.ace_eval_rewrite

前置:
    1. 后端已启动 localhost:8000
    2. Redis 已启动
    3. 不依赖知识库文档
"""
from __future__ import annotations

import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "eval_rewrite@qq.com"
TEST_PASSWORD = "123456"

TOPICS = [
    "人工智能在医疗诊断中的应用与挑战",
    "全球气候变化对农业的影响及应对策略",
    "区块链技术在供应链管理中的应用",
    "量子计算的发展现状与未来趋势",
    "新能源汽车技术路线对比分析",
]


async def _login(client: httpx.AsyncClient) -> tuple[str, int]:
    r = await client.post(f"{BASE_URL}/api/user/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    if r.status_code == 200 and r.json().get("success"):
        print(f"[账号] 登录: {TEST_EMAIL}")
    else:
        await client.post(f"{BASE_URL}/api/user/register", json={
            "username": "eval_rewrite_user", "email": TEST_EMAIL,
            "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD,
        })
        r = await client.post(f"{BASE_URL}/api/user/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        print(f"[账号] 注册并登录: {TEST_EMAIL}")
    data = r.json()["data"]
    return data["access_token"], int(data["user"]["id"])


async def _wait_plan(client: httpx.AsyncClient, headers: dict, conv_id: int, timeout: int = 120) -> dict | None:
    """等待 Planner 完成，返回 report 数据"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(3)
        r = await client.get(f"{BASE_URL}/api/chat/conversations/{conv_id}/report", headers=headers, timeout=10.0)
        if r.status_code == 200:
            data = r.json().get("data")
            if data and data.get("status") == "awaiting_confirm":
                return data
    return None


async def _wait_done(client: httpx.AsyncClient, headers: dict, timeout: int = 300) -> dict | None:
    """等待 report 完成，返回含 reviewer_rewrite_count 的数据"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        await asyncio.sleep(5)
        try:
            r = await client.get(f"{BASE_URL}/api/reports", headers=headers, timeout=10.0, follow_redirects=True)
            if r.status_code == 200 and r.text.strip():
                for rep in r.json().get("data", []):
                    if rep.get("status") in ("completed", "failed"):
                        return rep
        except Exception:
            pass
    return None


async def main():
    print(f"\n{'='*60}")
    print("  AceResearch 报告重写率评测")
    print('='*60)
    print(f"目标: {BASE_URL} | 报告: {len(TOPICS)} 篇 | 自动确认方案\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        token, user_id = await _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 清理旧对话
        r = await client.get(f"{BASE_URL}/api/chat/conversations", headers=headers)
        if r.status_code == 200:
            for c in r.json().get("data", []):
                await client.delete(f"{BASE_URL}/api/chat/conversations/{c['id']}", headers=headers, timeout=10.0)

        results = []
        total_rewrites = 0
        done = 0
        failed = 0

        print(f"{'#':>3}  {'主题':<46} {'状态':<10} {'重写':<6} {'耗时(s)'}")
        print("-" * 83)

        for i, topic in enumerate(TOPICS, 1):
            t0 = time.time()

            # 1. 创建对话 + 启动研究
            r = await client.post(f"{BASE_URL}/api/chat/conversations", json={"title": topic[:30], "mode": "research"}, headers=headers, timeout=15.0)
            if r.status_code != 200:
                print(f"  {i:>3}  {topic[:44]:<46} [错误] 创建对话")
                results.append({"topic": topic, "status": "error", "rewrites": 0, "elapsed": 0})
                continue
            conv_id = r.json()["data"]["id"]

            r = await client.post(f"{BASE_URL}/api/chat/send", json={"conversation_id": conv_id, "message": topic, "mode": "research"}, headers=headers, timeout=30.0)
            if r.status_code != 200:
                print(f"  {i:>3}  {topic[:44]:<46} [错误] 启动研究")
                results.append({"topic": topic, "status": "error", "rewrites": 0, "elapsed": 0})
                continue

            # 2. 等待 Planner → 自动确认
            plan = await _wait_plan(client, headers, conv_id)
            if not plan:
                print(f"  {i:>3}  {topic[:44]:<46} [超时] Planner")
                results.append({"topic": topic, "status": "timeout", "rewrites": 0, "elapsed": 0})
                continue

            report_id = plan.get("id") or plan.get("report_id")
            if report_id:
                await client.post(f"{BASE_URL}/api/chat/research/confirm", json={"conversation_id": conv_id, "report_id": report_id}, headers=headers, timeout=15.0)

            # 3. 等待完成
            rep = await _wait_done(client, headers, timeout=300)
            elapsed = time.time() - t0

            if rep is None:
                print(f"  {i:>3}  {topic[:44]:<46} [超时] 执行")
                results.append({"topic": topic, "status": "timeout", "rewrites": 0, "elapsed": round(elapsed, 1)})
                continue

            status = rep.get("status", "unknown")
            rw = rep.get("reviewer_rewrite_count", 0)
            total_rewrites += rw
            if status == "completed":
                done += 1
            else:
                failed += 1

            results.append({"topic": topic, "status": status, "rewrites": rw, "elapsed": round(elapsed, 1)})
            sd = {"completed": "✓ 完成", "failed": "✗ 失败"}.get(status, status)
            rwd = f"{rw}x" if rw else "0"
            print(f"  {i:>3}  {topic[:44]:<46} {sd:<10} {rwd:<6} {elapsed:.1f}s")

        rewrite_rate = total_rewrites / done * 100 if done else 0
        avg = sum(r["elapsed"] for r in results if r["status"] == "completed")
        avg = avg / done if done else 0

        print(f"\n{'='*60}")
        print(f"  完成: {done}  失败: {failed}  总重写: {total_rewrites}")
        print(f"  重写率: {rewrite_rate:.1f}%  平均耗时: {avg:.1f}s")
        print('='*60)

        out = os.path.join(os.path.dirname(__file__), "eval_rewrite.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total": len(TOPICS),
                "completed": done,
                "failed": failed,
                "total_rewrites": total_rewrites,
                "rewrite_rate": round(rewrite_rate, 1),
                "avg_elapsed": round(avg, 1),
                "details": results,
            }, f, ensure_ascii=False, indent=2)
        print(f"结果: {out}")


if __name__ == "__main__":
    asyncio.run(main())
