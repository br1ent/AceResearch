"""记忆提取节点：从对话中提取用户信息并更新 users.memory"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from config.agents import get_agent_settings
from config.prompts import get_prompt

settings = get_agent_settings()

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=0.2,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS,
)


def extract_memory_node(state: dict) -> dict:
    """从对话中提取记忆并更新用户 memory 字段"""
    user_id = state.get("user_id")
    dialogue = state.get("dialogue", "")
    existing_memory = state.get("existing_memory", "")

    if not dialogue or not user_id:
        return {"memory_updated": False, "memory_summary": existing_memory}

    # 加载系统提示词
    system_prompt = get_prompt("memory", "extract")
    if not system_prompt:
        return {"memory_updated": False, "memory_summary": existing_memory}

    # 拼接入参信息
    user_input = f"【现有记忆】\n{existing_memory}\n\n【当前对话】\n{dialogue}"
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input),
    ]

    response = llm.invoke(messages)
    text = response.content.strip()

    # 解析 JSON
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
        summary = data.get("memory_summary", "").strip()
        if summary:
            # 更新数据库
            from config.database import SessionLocal
            from models.user import User
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.memory = summary
                    db.commit()
                    return {"memory_updated": True, "memory_summary": summary}
            finally:
                db.close()
    except (json.JSONDecodeError, KeyError):
        pass

    return {"memory_updated": False, "memory_summary": existing_memory}
