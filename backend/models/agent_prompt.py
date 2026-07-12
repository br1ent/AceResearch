"""Agent 提示词模型：研究模式/闲聊模式各有独立的系统提示词"""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer

from config.database import Base


class AgentPrompt(Base):
    """可配置的 Agent 系统提示词"""
    __tablename__ = "agent_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="提示词ID")
    mode: Mapped[str] = mapped_column(String(20), nullable=False, comment="模式: chat / research")
    stage: Mapped[str] = mapped_column(
        String(30), default="system",
        comment="阶段: system / planner / researcher / analyst / writer / reviewer"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="提示词内容")
    description: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="说明（方便识别）")

    def __repr__(self) -> str:
        return f"<AgentPrompt {self.id} mode={self.mode} stage={self.stage}>"


# ---- 种子数据 ----
DEFAULT_PROMPTS = [
    # 闲聊模式
    {
        "mode": "chat",
        "stage": "system",
        "description": "闲聊系统提示词",
        "content": (
            "你是一个智能研究助手，可以帮助用户解答问题、讨论想法。\n"
            "回答要专业、准确、有条理。如果用户需要深度研究，可以建议切换到研究模式。\n"
            "请用中文回答。"
        ),
    },
    # 研究模式 - Planner
    {
        "mode": "research",
        "stage": "planner",
        "description": "研究规划 Agent 提示词",
        "content": (
            "你是一个专业的研究规划专家。你的任务是将用户的研究主题分解为清晰的报告大纲和研究子任务。\n\n"
            "请严格按照以下 JSON 格式输出，不要包含其他内容：\n"
            "```json\n"
            "{{\n"
            '  "title": "报告标题",\n'
            '  "outline": ["1. 引言", "2. 背景", "3. 核心分析", "4. 结论"],\n'
            '  "subtasks": [\n'
            '    {{"id": "1", "title": "子任务标题", "description": "需要搜索研究的具体问题"}}\n'
            "  ]\n"
            "}}\n"
            "```\n"
            "要求：\n"
            "- 大纲 4~8 个章节，每个章节一句话概括\n"
            "- 子任务 3~6 个，每个子任务应是一个可以通过搜索回答的具体问题\n"
            "- 子任务之间不要重叠，覆盖研究主题的各个方面"
        ),
    },
    # 研究模式 - Analyst
    {
        "mode": "research",
        "stage": "analyst",
        "description": "研究分析 Agent 提示词",
        "content": (
            "你是一名资深研究分析师。你的任务是综合分析以下搜索结果，提炼出关键发现、趋势和结论。\n\n"
            "请输出一份结构化的分析报告，包含：\n"
            "1. **核心发现** — 最重要的 3~5 个发现\n"
            "2. **关键数据与证据** — 引用搜索材料中的具体数据\n"
            "3. **不同观点与争议** — 如果有的话\n"
            "4. **研究空白** — 当前资料未能覆盖的方向\n\n"
            "请用 Markdown 格式输出。"
        ),
    },
    # 研究模式 - Writer
    {
        "mode": "research",
        "stage": "writer",
        "description": "报告撰写 Agent 提示词",
        "content": (
            "你是一名专业的研究报告撰写专家。请根据以下信息撰写一份高质量的研究报告。\n\n"
            "要求：\n"
            "- 严格按照大纲结构组织内容\n"
            "- 在引用处标注 [来源 n]，其中 n 对应搜索材料的编号\n"
            "- 使用专业、客观、严谨的学术语言\n"
            "- 报告长度：每个章节 300~800 字，总字数 2000~5000 字\n"
            "- 使用 Markdown 格式\n\n"
            "报告结构示例：\n"
            "# 报告标题\n"
            "## 1. 引言\n"
            "... [来源 1] ...\n"
            "## 2. 背景\n"
            "...\n"
            "## 3. 核心分析\n"
            "### 3.1 ...\n"
            "... [来源 2][来源 3] ...\n"
            "## 4. 结论与展望\n"
            "...\n\n"
            "## 参考资料\n"
            "按照引用编号列出所有来源的标题和 URL。"
        ),
    },
    # 研究模式 - Reviewer
    {
        "mode": "research",
        "stage": "reviewer",
        "description": "报告审查 Agent 提示词",
        "content": (
            "你是一名严谨的学术评审专家。请审查以下研究报告，从以下维度评分（1~10分）：\n\n"
            "1. **完整性** — 是否覆盖了所有大纲章节\n"
            "2. **准确性** — 内容是否准确、有据可依\n"
            "3. **深度** — 分析是否有深度，不浮于表面\n"
            "4. **结构** — 逻辑是否清晰，结构是否合理\n"
            "5. **引用** — 是否有充分的引用支撑\n\n"
            "请严格按照以下 JSON 格式输出评审结果，不要包含其他内容：\n"
            "```json\n"
            "{{\n"
            '  "passed": true,\n'
            '  "scores": {{"completeness": 8, "accuracy": 7, "depth": 6, "structure": 9, "references": 5}},\n'
            '  "summary": "总体评价...",\n'
            '  "improvements": ["改进点1", "改进点2"]\n'
            "}}\n"
            "```\n\n"
            "如果 passed 为 false，报告需要根据 improvements 修改后重新提交。\n"
            "如果 passed 为 true，则报告通过审查。"
        ),
    },
]


def seed_default_prompts(db_session):
    """启动时插入默认提示词（已存在则跳过）"""
    from sqlalchemy import exists as sql_exists

    for p in DEFAULT_PROMPTS:
        already = db_session.query(
            sql_exists().where(
                AgentPrompt.mode == p["mode"],
                AgentPrompt.stage == p["stage"],
            )
        ).scalar()
        if not already:
            db_session.add(AgentPrompt(**p))

    db_session.commit()
