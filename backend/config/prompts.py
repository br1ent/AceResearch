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
