"""闲聊/知识库上下文组装节点：从 DB 读取历史、记忆、提示词，组装 LLM 消息列表"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.chat.state import ChatState
from config.prompts import get_chat_system_prompt, get_knowledge_system_prompt
from config.database import SessionLocal


def build_context_node(state: ChatState) -> dict:
    """组装 LLM 所需的完整上下文"""
    conversation_id = state["conversation_id"]
    user_id = state["user_id"]
    mode = state.get("mode", "chat")

    # 1. 系统提示词
    if mode == "knowledge":
        system_prompt = get_knowledge_system_prompt()
    else:
        system_prompt = get_chat_system_prompt()

    # 2. 用户记忆（根据模式读取不同字段）
    memory_text = ""
    if user_id:
        db = SessionLocal()
        try:
            from models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                mem = user.kb_memory if mode == "knowledge" else user.memory
                if mem:
                    memory_text = mem
        finally:
            db.close()

    # 3. 历史消息
    db = SessionLocal()
    try:
        from services.chat.conversation import ConversationService
        conv_service = ConversationService(db)
        history = conv_service.get_messages(conversation_id, limit=20)
        history_dicts = [{"role": m.role, "content": m.content} for m in history]
    finally:
        db.close()

    # 4. 组装完整消息列表
    messages = [SystemMessage(content=system_prompt)]
    if memory_text:
        messages.append(SystemMessage(content=f"[用户画像]\n{memory_text}"))

    if mode == "knowledge":
        # 知识库模式：不拼接历史消息，每次独立检索
        messages.append(HumanMessage(content=state["user_message"]))
    else:
        # 历史消息（跳过最后一条，因为它是刚存入的 user_message，后面会单独加）
        for msg in history_dicts[:-1]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=state["user_message"]))

    return {
        "system_prompt": system_prompt,
        "memory_text": memory_text,
        "history": history_dicts,
        "messages": messages,
    }
