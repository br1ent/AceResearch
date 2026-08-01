# AceResearch 研思

> 基于 LangGraph 多 Agent 协作的深度研究平台

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AceResearch 是一个基于大语言模型的智能研究平台，通过多个 AI Agent 协作自动完成从规划、搜索到撰写报告的全流程深度研究。同时支持智能对话、联网搜索、个人知识库 RAG 问答等多种交互模式。

## 核心特性

- **多 Agent 协作** — Planner、Researcher、Analyst、Writer、Reviewer 五个 Agent 自动完成深度研究
- **研究流水线** — 主题规划 → 并行搜索 → 综合分析 → 报告撰写 → 质量审查（最多 2 次重写），全流程自动化
- **RAG 知识库** — 上传 Markdown 文档，语义分块 + 向量检索 + 重排序，精准文档问答
- **流式对话** — SSE 实时推送，用户即时看到 AI 回复内容
- **独立记忆** — 闲聊和知识库对话各自拥有独立记忆，知识库模式每轮独立检索无历史污染
- **Token 安全** — Redis 白名单机制，logout 后 Token 立即失效
- **查询缓存** — RAG 相同查询 10 分钟内直接返回缓存结果，减少 API 调用

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- DeepSeek API Key
- Tavily API Key
- 阿里云百炼 API Key（知识库需要）

### 安装 Redis

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 后端安装

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r ../requirements.txt
```

### 前端安装

```bash
cd frontend
npm install
```

### 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_research

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key

# Tavily（联网搜索）
TAVILY_API_KEY=your-tavily-api-key

# 嵌入 + 重排序（阿里云百炼，知识库需要）
EMBEDDING_API_KEY=sk-ws-xxx
RERANK_WORKSPACE_ID=llm-xxx
RERANK_MODEL=qwen3-rerank
RERANK_TOP_N=3

# 和风天气（可选）
QWEATHER_API_HOST=p86apyurp3.re.qweatherapi.com
QWEATHER_API_KEY=your-qweather-key
```

### 创建数据库

```sql
CREATE DATABASE smart_research CHARACTER SET utf8mb4;
```

### 启动服务

**后端**（自动创建数据库表）：

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**前端**（开发模式）：

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173 即可使用。

### 生产部署

```bash
cd frontend && npm run build
```

后端自动托管 `frontend/dist/` 静态文件，访问 http://localhost:8000 即可。

## 功能概览

| 功能 | 说明 |
|------|------|
| **闲聊模式** | DeepSeek + Tool Calling（联网搜索、天气、时间） |
| **研究模式** | 五 Agent 协作，主题规划 → 搜索 → 分析 → 撰写 → 审查 |
| **知识库 RAG** | Markdown 文档上传，语义分块 + 向量召回(10) + 重排序(3) |
| **实时进度** | WebSocket 推送研究进度，可视化每个 Agent 工作状态 |
| **Token 管理** | Redis 白名单，logout 后 Token 立即失效 |
| **查询缓存** | User 缓存 + RAG 查询缓存，减少 DB 和 API 调用 |

## 系统架构

```
┌───────────────────────────────────────────────────────┐
│                   前端 (Vue 3 + Vite)                    │
│       Tailwind CSS 4 + DaisyUI 5 + Pinia               │
├───────────────────────────────────────────────────────┤
│              SSE / WebSocket / REST                    │
├───────────────────────────────────────────────────────┤
│                  后端 (FastAPI)                          │
├────────────┬────────────────┬──────────────────────────┤
│  闲聊模式   │    研究模式      │     知识库 RAG           │
│ ChatGraph  │ Planning + Exec │  ChatGraph (KB Tools)   │
│ + ReAct    │   Workflow      │  + 语义分块 + 重排序      │
├────────────┴────────────────┴──────────────────────────┤
│               LangGraph (Agent 编排)                    │
├──────────────────────┬────────────────────────────────┤
│   MySQL (ORM)        │  ChromaDB (向量)  │  Redis (缓存) │
└──────────────────────┴───────────────────┴──────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI + Uvicorn |
| **AI 编排** | LangGraph + LangChain |
| **LLM** | DeepSeek (OpenAI 兼容接口) |
| **向量数据库** | ChromaDB |
| **嵌入模型** | 阿里云百炼 text-embedding-v4 (1024 维) |
| **重排序** | 阿里云百炼 qwen3-rerank (DashScope 标准 API) |
| **数据库** | MySQL + SQLAlchemy 2.0 |
| **缓存** | Redis (Token 白名单 / User 缓存 / RAG 缓存) |
| **搜索引擎** | Tavily Search API |
| **前端** | Vue 3 + Vite + Pinia + Tailwind CSS 4 + DaisyUI 5 |
| **认证** | JWT + BCrypt + Redis 黑名单 |

## 知识库 RAG

### 文档管理

- 仅支持 **Markdown (.md)** 文件上传
- 每用户最多 3 份文档，每份不超过 5MB
- 上传后异步解析 → 语义分块 → 向量化 → 存入 ChromaDB

### 语义分块

按 `##` / `###` Markdown 标题边界拆分文档，保持 `#` 文档标题作为上下文前缀附加到每个 chunk。超长 section 回退到 RecursiveCharacterTextSplitter 兜底，相邻短 section 自动合并避免碎片化。

### 检索流程

```
用户提问
  → 查询缓存 (Redis, TTL 10min) → 命中直接返回
  → Embedding 向量召回 10 条候选
  → qwen3-rerank 重排序 → 返回 Top-3
  → 写入缓存
  → 返回格式化文本
```

文档上传/删除时自动清空该用户的 RAG 缓存。

### 对话策略

知识库模式每轮**独立检索**，不拼接历史消息到上下文，避免 LLM 依赖上一轮的检索结果而跳过搜索。

### 评测

```bash
# RAG 检索准确率（Recall@3 / MRR）
cd backend && python -m backend.tests.ace_research_eval

# 完整评测（RAG 30 条 + 报告重写率 7 篇）
cd backend && python -m backend.tests.ace_eval_full
```

## 研究模式流程

```
用户提交主题
  → Planner 生成大纲 + 子任务
  → 用户确认/修改方案（WebSocket 推送）
  → Researcher 并行搜索资料（Tavily）
  → Analyst 综合分析结果
  → Writer 撰写报告
  → Reviewer 质量评估（最多重写 2 次）
  → Summarizer 生成摘要
  → 报告保存到"我的报告"
```

## Redis 缓存设计

| 功能 | Key | TTL | 说明 |
|------|-----|-----|------|
| Token 白名单 | `token:{jti}` | 与 JWT 一致 | logout 时删除，实现主动吊销 |
| User 缓存 | `user:{id}` | 5 分钟 | 避免每次请求 `SELECT` users |
| RAG 查询 | `rag:{uid}:{md5}` | 10 分钟 | 相同问题直接返回，省 embedding + rerank |

## 项目结构

```
AceResearch/
├── backend/
│   ├── main.py                   # FastAPI 入口，路由注册
│   ├── agents/
│   │   ├── chat/                 # 闲聊/知识库 Agent (ChatGraph + ReAct)
│   │   ├── research/             # 研究 Agent (Planner/Researcher/Analyst/Writer/Reviewer)
│   │   └── memory/               # 记忆提取 Agent
│   ├── services/
│   │   ├── chat/                 # 对话服务 (SSE 流式)
│   │   ├── research/             # 研究任务调度
│   │   ├── knowledge_base/       # 文档上传、语义分块、RAG 检索
│   │   └── user/                 # 用户服务
│   ├── routers/                  # FastAPI 路由 (REST + WebSocket)
│   ├── models/                   # SQLAlchemy ORM 模型
│   ├── schemas/                  # Pydantic Schema
│   ├── config/                   # 配置 (settings / agents / prompts / knowledge_base)
│   ├── utils/                    # 工具 (auth / ws_manager / redis)
│   └── tests/                    # 评测脚本
├── frontend/
│   └── src/
│       ├── views/                # 页面 (聊天 / 知识库 / 报告 / 用户)
│       ├── stores/               # Pinia 状态管理
│       ├── components/           # 通用组件
│       ├── router/               # 路由配置
│       └── js/                   # HTTP 客户端
├── requirements.txt
└── README.md
```

## API 路由

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/user/register` | 注册 |
| POST | `/api/user/login` | 登录，签发 JWT 并写入 Redis 白名单 |
| POST | `/api/user/logout` | 注销，删除 Redis 中所有 Token |
| POST | `/api/user/refresh` | 刷新 Access Token |
| POST | `/api/user/reset-password` | 重置密码 |
| GET  | `/api/user/me` | 获取当前用户信息 |
| PUT  | `/api/user/profile` | 更新个人资料（自动失效 User 缓存） |
| POST | `/api/user/avatar` | 上传头像 |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | `/api/chat/conversations` | 对话列表 |
| DELETE | `/api/chat/conversations/{id}` | 删除对话 |
| GET    | `/api/chat/conversations/{id}/messages` | 消息历史 |
| GET    | `/api/chat/conversations/{id}/report` | 获取研究报告 |
| POST   | `/api/chat/send` | 发起研究（WebSocket 进度） |
| POST   | `/api/chat/send/stream` | 闲聊/知识库流式输出（SSE） |

### 研究

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/research/confirm` | 确认方案，开始执行 |
| POST | `/api/chat/research/revise` | 修改方案，重新规划 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | `/api/kb/documents` | 文档列表 |
| GET    | `/api/kb/documents/count` | 文档数量 |
| POST   | `/api/kb/documents/upload` | 上传文档（仅 .md） |
| DELETE | `/api/kb/documents/{id}` | 删除文档（清空 RAG 缓存） |

### 报告

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | `/api/reports/` | 报告列表 |
| GET    | `/api/reports/{id}` | 报告详情 |
| DELETE | `/api/reports/{id}` | 删除报告 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/{conversation_id}?token=...` | 研究进度实时推送 |

## 环境变量

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `DB_HOST` | MySQL 地址 | `localhost` | 是 |
| `DB_PORT` | MySQL 端口 | `3306` | 是 |
| `DB_USER` | MySQL 用户名 | `root` | 是 |
| `DB_PASSWORD` | MySQL 密码 | - | 是 |
| `DB_NAME` | 数据库名 | `smart_research` | 是 |
| `SECRET_KEY` | JWT 密钥 | - | 是 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期（分钟） | `30` | 否 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 过期（天） | `7` | 否 |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` | 是 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | 是 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1` | 否 |
| `DEEPSEEK_MODEL` | 模型名 | `deepseek-v4-flash` | 否 |
| `DEEPSEEK_MAX_TOKENS` | 最大输出 Token | `8192` | 否 |
| `TAVILY_API_KEY` | Tavily 搜索 Key | - | 是 |
| `EMBEDDING_API_KEY` | 百炼 API Key | - | 知识库需要 |
| `RERANK_WORKSPACE_ID` | 百炼 Workspace ID | - | 知识库需要 |
| `RERANK_MODEL` | 重排序模型 | `qwen3-rerank` | 否 |
| `RERANK_TOP_N` | 重排序返回条数 | `3` | 否 |
| `CHUNK_SIZE` | 分块大小（字符） | `800` | 否 |
| `CHUNK_OVERLAP` | 分块重叠（字符） | `100` | 否 |
| `RECALL_K` | 向量召回条数 | `10` | 否 |
| `MAX_DOCUMENTS_PER_USER` | 每用户文档上限 | `3` | 否 |
| `MAX_FILE_SIZE_MB` | 上传文件上限（MB） | `5` | 否 |
| `QWEATHER_API_HOST` | 和风天气 Host | - | 否 |
| `QWEATHER_API_KEY` | 和风天气 Key | - | 否 |

## 数据模型

### MySQL

| 表 | 说明 | 关键字段 |
|----|------|----------|
| `users` | 用户 | id, username, email, password_hash, photo, memory, kb_memory |
| `conversations` | 对话 | id, user_id, title, mode (chat/research/knowledge) |
| `messages` | 消息 | id, conversation_id, role, content, msg_type |
| `reports` | 报告 | id, conversation_id, title, content, status, reviewer_rewrite_count |
| `knowledge_documents` | 文档 | id, user_id, title, file_type, chunk_count, status |
| `agent_prompts` | 提示词 | id, mode, stage, content |

### ChromaDB

每个用户独立 collection（`user_{id}_kb`），存储文档语义分块的 1024 维向量，支持 top-k 检索 + 重排序。

## 许可证

MIT License
