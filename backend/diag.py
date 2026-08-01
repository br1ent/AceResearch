"""
诊断脚本：测试知识库检索是否正常工作
直接输出到 result.txt，避免编码问题
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import httpx, asyncio
from services.knowledge_base.retrieval_service import search_knowledge


async def main():
    # 登录
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "http://localhost:8000/api/user/login",
            json={"email": "brent@qq.com", "password": "123456"},
        )
        data = r.json()
        token = data["data"]["access_token"]
        user_id = int(data["data"]["user"]["id"])

        # 查文档
        r2 = await client.get(
            "http://localhost:8000/api/kb/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        docs = r2.json().get("data", [])
        doc_info = "\n".join(
            f"  id={d['id']} title={d['title']} status={d['status']}"
            for d in docs
        )

        # 测试检索
        test_cases = [
            ("2.6.13", "Spring Boot 版本号是多少"),
            ("000000", "数据库连接密码是什么"),
            ("AcGameObject", "游戏对象基类叫什么"),
            ("Nashorn", "AI 代码用什么引擎执行"),
            ("3000", "后端服务端口是多少"),
            ("MyBatis", "数据库操作用的什么框架"),
            ("Maven", "项目构建工具是什么"),
            ("csrf", "Spring Security 禁用了什么安全机制"),
        ]

        lines = []
        lines.append(f"user_id = {user_id}")
        lines.append(f"docs:\n{doc_info}")
        lines.append("")

        for kw, query in test_cases:
            raw = search_knowledge(user_id, query, top_k=3)
            hit = kw.lower() in raw.lower()
            lines.append(f"keyword: {kw}")
            lines.append(f"query: {query}")
            lines.append(f"hit: {hit}")
            lines.append(f"result length: {len(raw)}")
            lines.append(f"result preview: {raw[:300]}")
            lines.append("")

        output = "\n".join(lines)

        out_path = os.path.join(os.path.dirname(__file__), "result.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"done, see {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
