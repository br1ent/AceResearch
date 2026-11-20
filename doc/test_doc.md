# AceResearch 研思 — 技术文档

## 项目概述

AceResearch（研思）是一个基于 LangGraph 多 Agent 协作的深度研究平台。后端使用 FastAPI 框架，前端使用 Vue 3 + Vite 构建。

## 技术架构

### 后端技术栈

后端框架是 FastAPI，运行在 Uvicorn 上，默认端口 8000。数据库使用 MySQL 8.0，通过 SQLAlchemy 2.0 ORM 进行数据操作，数据库驱动是 PyMySQL。

认证系统使用 JWT 方案，密码哈希使用 BCrypt 算法，JWT 密钥算法为 HS256。Access Token 有效期默认 30 分钟，Refresh Token 有效期默认 7 天。Token 签发后写入 Redis 白名单，注销时从 Redis 删除，实现主动吊销。

### AI 模型配置

大语言模型使用 DeepSeek，默认模型为 deepseek-v4-flash，通过 OpenAI 兼容接口调用。嵌入模型使用阿里云百炼 text-embedding-v4，输出 1024 维向量。重排序模型使用阿里云百炼 qwen3-rerank，通过 DashScope 标准 API 调用。

Agent 温度参数：Planner 使用 0.5，Writer 使用 0.6，对话模式使用 0.7。最大输出 Token 数为 8192。

### 前端技术栈

前端使用 Vue 3 搭配 Vite 构建工具，默认开发端口 5173。UI 框架使用 Tailwind CSS 4 和 DaisyUI 5 组件库。状态管理使用 Pinia，路由管理使用 Vue Router。

## Agent 编排

### 研究模式流程

研究模式包含五个 Agent 协作：

1. **Planner**：分析研究主题，生成报告大纲和子任务列表
2. **Researcher**：并行搜索资料，每个子任务通过 Tavily Search API 获取最多 5 条结果
3. **Analyst**：综合分析所有搜索结果，提炼关键发现
4. **Writer**：根据大纲和分析结果撰写完整报告
5. **Reviewer**：从完整性、准确性、深度等维度评估报告质量

Reviewer 最多触发 2 次重写循环。如果 Reviewer 判定不通过，Writer 根据审查意见修改后再次提交审查。

### 对话模式

对话模式使用 ChatGraph + ReAct 循环，LLM 绑定工具后循环调用，最多 5 次迭代。支持的工具包括：获取当前时间、查询天气、联网搜索。

### 知识库模式

知识库模式同样使用 ChatGraph，但仅绑定知识库搜索工具，不绑定联网搜索。每次提问独立检索，不拼接历史消息，避免 LLM 依赖上一轮的检索结果。

## 知识库 RAG

### 文档处理

仅支持 Markdown 格式文件上传，每用户最多 3 份文档，每份不超过 5MB。上传后异步处理：解析 → 语义分块 → 向量化 → 存入 ChromaDB。

语义分块按 Markdown 标题边界切分，优先按 H2 标题拆分，超长 section 再按 H3 细分。chunk_size 默认 800 字符，chunk_overlap 默认 100 字符。

### 检索流程

向量数据库使用 ChromaDB，每个用户独立一个 collection。检索时先向量召回 10 条候选，再通过 qwen3-rerank 重排序返回 Top-3 结果。

相同查询的结果缓存到 Redis，TTL 10 分钟。上传或删除文档时自动清空该用户的 RAG 缓存。

### 嵌入与重排序

嵌入模型 text-embedding-v4 通过阿里云百炼 API 调用，每次最多批量处理 10 条文本。重排序使用 DashScope 标准 API 端点。

## 缓存系统

项目使用 Redis 作为缓存层，连接地址默认为 redis://localhost:6379/0。

Redis 缓存三层设计：

1. **Token 白名单**：key 为 token:{jti}，TTL 与 JWT 一致。每次请求校验 token 是否在白名单中，注销时删除。
2. **User 缓存**：key 为 user:{id}，TTL 5 分钟。缓存用户 id、email、username、photo 字段。
3. **RAG 查询缓存**：key 为 rag:{user_id}:{md5}，TTL 10 分钟。相同查询直接返回缓存结果。

## 配置参数

### 知识库配置

- CHUNK_SIZE: 800
- CHUNK_OVERLAP: 100
- MAX_DOCUMENTS_PER_USER: 3
- MAX_FILE_SIZE_MB: 5
- RECALL_K: 10
- EMBEDDING_MODEL: text-embedding-v4
- RERANK_MODEL: qwen3-rerank
- RERANK_TOP_N: 3

### Agent 配置

- DEEPSEEK_MODEL: deepseek-v4-flash
- PLANNER_TEMPERATURE: 0.5
- WRITER_TEMPERATURE: 0.6
- DEEPSEEK_TEMPERATURE: 0.7
- REVIEWER_MAX_RETRIES: 2
- CHAT_MAX_ITERATIONS: 5
- RESEARCHER_MAX_RESULTS: 5
- DEEPSEEK_MAX_TOKENS: 8192

## API 端点

认证相关：注册 `/api/user/register`，登录 `/api/user/login`，注销 `/api/user/logout`，刷新 Token `/api/user/refresh`，获取用户信息 `/api/user/me`。

对话相关：对话列表 `/api/chat/conversations`，消息历史 `/api/chat/conversations/{id}/messages`，研究启动 `/api/chat/send`，流式对话 `/api/chat/send/stream`，方案确认 `/api/chat/research/confirm`，方案修改 `/api/chat/research/revise`。

知识库相关：文档列表 `/api/kb/documents`，文档上传 `/api/kb/documents/upload`，文档删除 `/api/kb/documents/{id}`。

报告相关：报告列表 `/api/reports/`，报告详情 `/api/reports/{id}`，报告删除 `/api/reports/{id}`。

WebSocket：研究进度通过 `/ws/{conversation_id}` 实时推送。

## 数据库设计

MySQL 数据库名为 smart_research，字符集 utf8mb4。主要表结构：

- users: 用户表，含 id、email、username、password_hash、photo、memory、kb_memory
- conversations: 对话表，含 id、user_id、title、mode（chat/research/knowledge）
- messages: 消息表，含 id、conversation_id、role、content、msg_type
- reports: 报告表，含 id、conversation_id、title、content、status、reviewer_rewrite_count
- knowledge_documents: 文档表，含 id、user_id、title、file_type、chunk_count、status
- agent_prompts: 提示词表，含 id、mode、stage、content

## 搜索引擎

联网搜索使用 Tavily Search API，通过 langchain-community 的 TavilySearchResults 工具集成，每次搜索返回最多 3 条结果。

## 天气服务

天气查询使用和风天气 QWeather API v7 版本，先通过 GeoAPI 将城市名转为 LocationID，再查询实时天气数据。
