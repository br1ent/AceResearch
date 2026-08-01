"""
AceResearch RAG 检索准确率评测（30 条查询）

运行:
    cd AceResearch/backend
    python -m backend.tests.ace_eval_rag

前置:
    1. 后端已启动 localhost:8000
    2. 已上传 test_doc.md 到知识库并处理完毕
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
TEST_EMAIL = "eval_rag@qq.com"
TEST_PASSWORD = "123456"
TOP_K = 3

RAG_QUERIES = [
    ("后端使用什么Python框架", "FastAPI"),
    ("后端服务运行在什么服务器上", "Uvicorn"),
    ("后端默认端口是多少", "8000"),
    ("数据库使用什么系统", "MySQL"),
    ("ORM框架是什么", "SQLAlchemy"),
    ("数据库驱动是什么", "PyMySQL"),
    ("数据库名是什么", "smart_research"),
    ("数据库字符集是什么", "utf8mb4"),
    ("密码哈希使用什么算法", "BCrypt"),
    ("JWT签名算法是什么", "HS256"),
    ("大语言模型使用什么", "DeepSeek"),
    ("默认模型名称是什么", "deepseek-v4-flash"),
    ("嵌入模型是什么", "text-embedding-v4"),
    ("重排序模型是什么", "qwen3-rerank"),
    ("嵌入向量维度是多少", "1024"),
    ("最大输出Token是多少", "8192"),
    ("Planner的温度参数是多少", "0.5"),
    ("Writer的温度参数是多少", "0.6"),
    ("对话模式温度参数是多少", "0.7"),
    ("Reviewer最多重试几次", "2"),
    ("聊天模式最多迭代几次", "5"),
    ("每次搜索最多返回几条结果", "5"),
    ("前端构建工具是什么", "Vite"),
    ("前端开发端口是多少", "5173"),
    ("UI组件库是什么", "DaisyUI"),
    ("CSS框架是什么", "Tailwind"),
    ("状态管理用什么", "Pinia"),
    ("路由管理用什么", "Vue Router"),
    ("文档分块大小是多少", "800"),
    ("向量召回多少条候选", "10"),
    ("重排序后返回多少条", "3"),
]


async def main():
    print(f"\n{'='*60}")
    print("  AceResearch RAG 检索准确率评测")
    print('='*60)
    print(f"目标: {BASE_URL} | 查询: {len(RAG_QUERIES)} 条 | TOP_K: {TOP_K}\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # ── 登录 ──
        r = await client.post(f"{BASE_URL}/api/user/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if r.status_code == 200 and r.json().get("success"):
            print(f"[账号] 登录: {TEST_EMAIL}")
        else:
            await client.post(f"{BASE_URL}/api/user/register", json={
                "username": "eval_rag_user", "email": TEST_EMAIL,
                "password": TEST_PASSWORD, "confirm_password": TEST_PASSWORD,
            })
            r = await client.post(f"{BASE_URL}/api/user/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
            print(f"[账号] 注册并登录: {TEST_EMAIL}")

        data = r.json()["data"]
        token = data["access_token"]
        user_id = int(data["user"]["id"])
        headers = {"Authorization": f"Bearer {token}"}

        # ── 等待文档就绪 ──
        print("[知识库] 等待文档处理完毕...")
        doc_names = []
        for _ in range(12):
            await asyncio.sleep(5)
            r = await client.get(f"{BASE_URL}/api/kb/documents", headers=headers)
            if r.status_code == 200:
                docs = r.json().get("data", [])
                done = [d for d in docs if d.get("status") == "completed"]
                if done:
                    doc_names = [d.get("title", "?") for d in done]
                    print(f"[知识库] {len(done)} 篇就绪: {', '.join(doc_names)}\n")
                    break
        else:
            print("[警告] 文档未就绪，继续评测\n")

        # ── 检索评测 ──
        from services.knowledge_base.retrieval_service import search_knowledge

        recalls, mrrs, details = [], [], []
        print(f"{'#':>3}  {'查询':<38} {'关键词':<16} {'结果'}")
        print("-" * 75)

        for i, (query, kw) in enumerate(RAG_QUERIES, 1):
            raw = search_knowledge(user_id, query, top_k=TOP_K)
            hit = kw.lower() in raw.lower()
            mrr = 0.0
            if hit:
                for rank, src in enumerate(raw.lower().split("[来源")[1:], 1):
                    if kw.lower() in src:
                        mrr = 1.0 / rank
                        break

            recalls.append(1 if hit else 0)
            mrrs.append(mrr)
            details.append({"query": query, "keyword": kw, "hit": hit, "mrr": mrr})
            print(f"  {i:>3}  {query[:36]:<38} {kw:<16} {'✓' if hit else '✗'}  MRR={mrr:.2f}")

        recall = sum(recalls) / len(recalls) * 100
        mrr_score = sum(mrrs) / len(mrrs) * 100

        print(f"\n{'='*60}")
        print(f"  Recall@{TOP_K}:  {recall:.1f}%  ({sum(recalls)}/{len(RAG_QUERIES)})")
        print(f"  MRR@{TOP_K}:     {mrr_score:.1f}%")
        print(f"  文档: {', '.join(doc_names)}")
        print('='*60)

        out = os.path.join(os.path.dirname(__file__), "eval_rag.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "documents": doc_names,
                f"recall@{TOP_K}": round(recall, 1),
                f"mrr@{TOP_K}": round(mrr_score, 1),
                "hit_count": sum(recalls),
                "total": len(RAG_QUERIES),
                "details": details,
            }, f, ensure_ascii=False, indent=2)
        print(f"结果: {out}")


if __name__ == "__main__":
    asyncio.run(main())
