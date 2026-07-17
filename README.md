# AceResearch 研思

> 基于 LangGraph 多 Agent 协作的深度研究平台

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目简介

AceResearch 是一个基于大语言模型的智能研究平台，通过多个 AI Agent 协作自动完成从规划、搜索、分析到撰写报告的全流程深度研究。平台同时支持智能对话、联网搜索、个人知识库检索等多种交互模式，为用户提供一站式的知识获取和研究辅助服务。

### 核心亮点

- **多 Agent 协作** — Planner、Researcher、Analyst、Writer、Reviewer 五个 Agent 自动协作，模拟人类研究流程
- **研究流水线** — 主题规划 → 联网搜索 → 综合分析 → 报告撰写 → 质量审查，全流程自动化
- **RAG 知识库** — 上传个人文档，通过向量检索 + 重排序技术精准回答文档相关问题
- **流式对话** — SSE 实时推送，用户即时看到 AI 回复内容
- **记忆系统** — 闲聊和知识库对话各自拥有独立记忆，提升长对话体验

## 功能概览

| 功能 | 说明 |
|---|---|
| 闲聊模式 | DeepSeek 大模型驱动，支持联网搜索（Tavily）、天气查询（和风天气）、实时时间等 Tool Calling |
| 研究模式 | 五 Agent 协作，自动规划任务、并行搜索资料、智能分析提炼、撰写高质量报告、AI 自主审查修正 |
| 个人文档检索 | 支持 PDF/TXT/MD/DOCX 上传，文本分块 + 阿里云百炼 Embedding + ChromaDB 向量存储 + qwen3-rerank 重排序，精准问答 |
| 研究方案审批 | Planner 生成大纲后由用户确认或修改，人机协作确保研究方向和深度符合预期 |
| 实时进度反馈 | WebSocket 推送研究进度，可视化展示每个 Agent 的工作状态 |

## 系统架构

```
┌──────────────────────────────────────────────────┐
│                   前端 (Vue 3)                     │
│   DaisyUI + Tailwind CSS + Pinia + Vue Router     │
├──────────────────────────────────────────────────┤
│               SSE / WebSocket / REST              │
├──────────────────────────────────────────────────┤
│                 后端 (FastAPI)                     │
├──────────┬──────────────────┬────────────────────┤
│ 闲聊模式  │    研究模式        │   个人文档检索      │
│ ChatGraph │ PlanningWorkflow  │   ChatGraph + RAG  │
│ + ReAct   │ + ExecutionWorkflow│   + KB Tools       │
├──────────┴──────────────────┴────────────────────┤
│               LangGraph (Agent 编排)               │
├──────────────────────────────────────────────────┤
│     MySQL (ORM)    │   ChromaDB (向量数据库)       │
└──────────────────────────────────────────────────┘
```

## 研究模式 Agent 工作流

```
用户输入主题
    │
    ▼
 Planner ──────────► 生成大纲 + 子任务
    │
    ▼
 用户确认 ──────────► plan_ready
    │
    ▼
 Researcher ────────► 并行搜索 (Tavily)
    │
    ▼
 Analyst ───────────► 综合分析搜索结果
    │
    ▼
 Writer ────────────► 撰写 Markdown 报告
    │
    ▼
 Reviewer ──────────► AI 审查 + 反馈
    │                    │
    │              passed? ── 否 ──► Writer (重写)
    │                    │
    是                   │
    │                    ▼
    ▼               report_completed
 report_completed
```

## 技术栈

**前端**

| 技术 | 用途 |
|---|---|
| Vue 3 | 渐进式前端框架 |
| Vite | 构建工具 |
| Tailwind CSS + DaisyUI | UI 组件库 |
| Pinia | 状态管理 |
| Vue Router | 路由 |
| Lucide | 图标库 |

**后端**

| 技术 | 用途 |
|---|---|
| FastAPI | Web 框架 |
| SQLAlchemy + PyMySQL | ORM + 数据库 |
| LangGraph | 多 Agent 有状态编排 |
| LangChain | LLM 应用框架 |
| ChromaDB | 向量数据库 |
| WebSocket | 实时研究进度推送 |
| SSE | 流式对话输出 |

**AI/搜索服务**

| 技术 | 用途 |
|---|---|
| DeepSeek V4 (Flash) | LLM 推理 |
| Tavily Search API | 联网搜索 |
| 阿里云百炼 text-embedding-v4 | 文本向量化 |
| 阿里云百炼 qwen3-rerank | 重排序 |
| 和风天气 QWeather API | 天气查询 |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+

### 后端启动

```bash
cd SmartResearchAssistant/backend

# 创建并激活虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 安装依赖
pip install -r ../requirements.txt

# 编辑 .env 配置文件（DEEPSEEK_API_KEY, TAVILY_API_KEY 等）

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd SmartResearchAssistant/frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 环境变量

| 变量 | 说明 | 必填 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 是 |
| `TAVILY_API_KEY` | Tavily 搜索 API Key | 是 |
| `EMBEDDING_API_KEY` | 阿里云百炼 DashScope API Key | 知识库需要 |
| `QWEATHER_API_HOST` | 和风天气 API Host | 否 |
| `QWEATHER_API_KEY` | 和风天气 API Key | 否 |
| `DB_HOST` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 数据库连接 | 是 |
| `SECRET_KEY` | JWT 加密密钥 | 是 |

## 项目结构

```
SmartResearchAssistant/
├── backend/
│   ├── agents/                # Agent 定义（LangGraph 图结构）
│   │   ├── chat/              #   闲聊模式 Agent
│   │   ├── research/          #   研究模式 Agent (Planner/Researcher/Analyst/Writer/Reviewer)
│   │   └── memory/            #   记忆提取 Agent
│   ├── services/              # 业务逻辑服务
│   │   ├── chat/              #   聊天服务
│   │   ├── research/          #   研究服务
│   │   └── knowledge_base/    #   知识库服务（上传/分块/向量化/检索）
│   ├── routers/               # API 路由
│   ├── models/                # 数据库模型 (SQLAlchemy ORM)
│   ├── config/                # 配置管理
│   ├── schemas/               # Pydantic 数据校验
│   ├── utils/                 # 认证、WebSocket 管理
│   └── main.py                # FastAPI 应用入口
├── frontend/
│   └── src/
│       ├── views/             # 页面组件
│       │   ├── chat/          #   聊天页面 + 子组件
│       │   ├── home/          #   首页
│       │   ├── knowledge/     #   文档管理页
│       │   ├── report/        #   报告列表/详情
│       │   └── user/          #   个人资料页
│       ├── stores/            # Pinia 状态管理
│       ├── components/        # 共享组件 (导航栏等)
│       ├── router/            # Vue Router 配置
│       └── js/http/           # Axios 封装 (JWT 自动刷新)
├── requirements.txt           # Python 依赖
└── README.md
```

## 许可证

MIT License
