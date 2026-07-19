"""从数据库加载 Agent 提示词"""
from functools import lru_cache

from config.database import SessionLocal
from models.agent_prompt import AgentPrompt


def get_prompt(mode: str, stage: str = "system") -> str:
    """获取指定模式/阶段的提示词，未配置则返回空字符串"""
    db = SessionLocal()
    try:
        prompt = (
            db.query(AgentPrompt)
            .filter(AgentPrompt.mode == mode, AgentPrompt.stage == stage)
            .first()
        )
        return prompt.content if prompt else ""
    finally:
        db.close()


def get_chat_system_prompt() -> str:
    """闲聊模式的系统提示词"""
    prompt = get_prompt("chat", "system")
    if not prompt:
        prompt = "你是一个智能研究助手，帮助用户解答问题。请用中文回答。"
    return prompt


def get_research_prompt(stage: str) -> str:
    """研究模式指定阶段的提示词"""
    return get_prompt("research", stage)


def get_knowledge_system_prompt() -> str:
    """知识检索模式的系统提示词"""
    prompt = get_prompt("knowledge", "system")
    if not prompt:
        prompt = "你是一个文档问答助手。请根据用户上传的文档内容回答问题，使用纯文本格式，不要使用Markdown。"
    return prompt


def get_summarizer_prompt() -> str:
    """研究报告生成后的自动总结提示词"""
    prompt = get_prompt("research", "summarizer")
    if not prompt:
        prompt = (
            "你是一个研究助手。请根据以下研究报告，生成一段简洁的总结消息，格式如下：\n\n"
            "📄 研究报告已生成\n\n"
            "标题：<报告标题>\n"
            "本次研究围绕 <一句话描述研究主题>，覆盖以下方面：<用 3~5 句话概括研究了什么、有哪些重要发现/结论>\n"
            "报告已保存到「我的报告」页面。\n\n"
            "要求：语言自然流畅，不罗列大纲条目，只描述研究收获。"
        )
    return prompt
