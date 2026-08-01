"""
AceResearch 知识库检索质量评测脚本
评测 Recall@3 / MRR，~3 分钟内完成

运行方式（项目根目录）：
    python -m backend.tests.ace_research_eval

依赖：httpx, asyncio（标准库）
"""
from __future__ import annotations

import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

# ─── 配置 ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "brent@qq.com"
TEST_PASSWORD = "123456"
TOP_K = 3

# (query, 期望命中的关键词)
# 命中：检索结果中任意一个来源文档的标题或内容包含该关键词
KB_QUERIES = [
    ("Spring Boot 版本号是多少", "2.6.13"),
    ("后端服务端口是多少", "3000"),
    ("JWT Token 有效期是多久", "JWT_TTL"),
    ("密码是用什么加密的", "BCrypt"),
    ("数据库连接密码是什么", "000000"),
    ("数据库名是哪个", "kob"),
    ("WebSocket 路径是什么", "websocket"),
    ("游戏地图行列数分别是多少", "15"),
    ("匹配系统服务端口号", "3001"),
    ("Bot 运行系统端口号", "3002"),
    ("MySQL 默认端口号", "3306"),
    ("Vue 前端开发服务器端口", "5173"),
    ("Vite 代理目标地址是什么", "127.0.0.1:3000"),
    ("Vuex 有哪些模块", "ModuleUser"),
    ("Vue Router 用什么做权限控制", "beforeEach"),
    ("游戏循环用什么实现动画", "requestAnimationFrame"),
    ("Canvas 绘制蛇用的是什么方法", "arc"),
    ("数据库操作用的什么框架", "MyBatis"),
    ("JWT 认证方式是什么", "STATELESS"),
    ("微服务有哪些模块", "matchingsystem"),
    ("AI 代码用什么引擎执行", "Nashorn"),
    ("Lombok 用了哪些注解", "Data"),
    ("FastJSON 用来做什么", "JSONObject"),
    ("Vue 组合式 API 叫什么", "Composition API"),
    ("代码编辑器用的什么组件", "Ace Editor"),
    ("项目构建工具是什么", "Maven"),
    ("Spring Security 禁用了什么安全机制", "csrf"),
    ("游戏对象基类叫什么", "AcGameObject"),
    ("数据库连接池怎么配置", "pool"),
    ("JWT 签名用的 key 变量名是什么", "secretKey"),
]


async def main():
    print(f"\n{'='*50}")
    print("  AceResearch 知识库检索质量评测")
    print('='*50)
    print(f"目标服务: {BASE_URL}")
    print(f"查询数量: {len(KB_QUERIES)} 条 | TOP_K: {TOP_K}")
    print(f"预计耗时: ~3 分钟\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
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
                    "username": "eval_user",
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
                print(f"[账号] 注册并登录成功")
            else:
                print(f"[账号] 登录失败: {login_resp.text}")
                return

        headers = {"Authorization": f"Bearer {token}"}

        # 等待文档处理完毕
        print("[知识库] 等待文档处理完毕...")
        for _ in range(12):
            await asyncio.sleep(5)
            r_list = await client.get(f"{BASE_URL}/api/kb/documents", headers=headers)
            if r_list.status_code == 200:
                docs = r_list.json().get("data", [])
                if docs and all(d.get("status") == "completed" for d in docs):
                    doc_names = [d.get("title", "?") for d in docs]
                    print(f"[知识库] {len(docs)} 篇文档处理完毕\n")
                    break
        else:
            docs = r_list.json().get("data", []) if r_list.status_code == 200 else []
            doc_names = [d.get("title", "?") for d in docs if d.get("status") == "completed"]
            print(f"[警告] 部分文档可能未处理完成，继续评测\n")

        # 执行检索评测
        print(f"[评测] 开始检索评测（共 {len(KB_QUERIES)} 条查询）")
        print(f"{'#':>3}  {'查询':<36} {'关键词':<18} {'结果'}")
        print("-" * 74)

        from services.knowledge_base.retrieval_service import search_knowledge

        recalls: list[int] = []
        mrrs: list[float] = []
        hit_details: list[dict] = []

        for i, (query, keyword) in enumerate(KB_QUERIES, 1):
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
            print(f"  {i:>3}  {query[:34]:<36} {keyword:<18} {mark}  MRR={mrr:.2f}")

        recall_at_k = sum(recalls) / len(recalls) * 100
        mrr_score = sum(mrrs) / len(mrrs) * 100
        hit_count = sum(recalls)

        print(f"\n{'='*50}")
        print("  评测结果汇总")
        print('='*50)
        print(f"  上传文档:      {', '.join(doc_names)}")
        print(f"  查询数量:      {len(KB_QUERIES)}")
        print(f"  命中数量:      {hit_count} / {len(KB_QUERIES)}")
        print(f"  Recall@{TOP_K}:     {recall_at_k:.1f}%")
        print(f"  MRR@{TOP_K}:        {mrr_score:.1f}%")
        print('='*50)

        result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "docs": doc_names,
            "total_queries": len(KB_QUERIES),
            "hit_count": hit_count,
            f"recall@{TOP_K}": round(recall_at_k, 1),
            f"mrr@{TOP_K}": round(mrr_score, 1),
            "details": hit_details,
        }

        out_path = os.path.join(os.path.dirname(__file__), "eval_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())