"""闲聊/知识库上下文组装节点：从 DB 读取历史、记忆、提示词，组装 LLM 消息列表"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.chat.state import ChatState
from config.prompts import get_chat_system_prompt
from config.database import SessionLocal


def build_context_node(state: ChatState) -> dict:
    """组装 LLM 所需的完整上下文"""
    conversation_id = state["conversation_id"]
    user_id = state["user_id"]
    mode = state.get("mode", "chat")

    # 1. 系统提示词
    system_prompt = get_chat_system_prompt()
    if mode == "knowledge":
        system_prompt += "\n\n你是一个基于个人文档的知识库问答助手。用户已上传了包含重要信息的文档。对于用户的任何提问，你必须首先调用 search_knowledge_base 工具检索文档内容，然后基于检索结果回答。只有当工具返回'知识库中没有文档内容'时，才使用你的通用知识。"

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

    # 历史消息（跳过最后一条，因为它是刚存入的 user_message，后面会单独加）
    for msg in history_dicts[:-1]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # 当前用户消息
    messages.append(HumanMessage(content=state["user_message"]))

    return {
        "system_prompt": system_prompt,
        "memory_text": memory_text,
        "history": history_dicts,
        "messages": messages,
    }
