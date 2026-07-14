"""闲聊服务：使用 LangGraph ChatGraph 调用 DeepSeek"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.agents import get_agent_settings
from config.prompts import get_chat_system_prompt
from agents.chat_graph import ChatGraph
from services.chat.conversation_service import ConversationService

settings = get_agent_settings()

# 流式用的 LLM（ChatGraph 内部也有自己的 LLM）
stream_llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=settings.DEEPSEEK_TEMPERATURE,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS,
)

chat_graph = ChatGraph()


class ChatService:
    def __init__(self, db_session):
        self.conv_service = ConversationService(db_session)
        self.db = db_session

    async def chat(self, conversation_id: int, user_message: str) -> str:
        """非流式对话：通过 ChatGraph 调用 LLM"""
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=user_message, msg_type="text")
        history = self.conv_service.get_messages(conversation_id, limit=20)

        hist_list = [{"role": m.role, "content": m.content} for m in history[:-1]]
        result = await chat_graph.ainvoke({
            "conversation_id": conversation_id,
            "user_message": user_message,
            "history": hist_list,
            "reply": "",
        })
        reply = result["reply"]

        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content=reply, msg_type="text")
        return reply

    async def chat_stream(self, conversation_id: int, user_message: str):
        """流式对话：保存消息 → 逐 token 返回 → 保存完整回复"""
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=user_message, msg_type="text")
        history = self.conv_service.get_messages(conversation_id, limit=20)

        system_prompt = get_chat_system_prompt()
        messages = [SystemMessage(content=system_prompt)]
        for msg in history[:-1]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        # 加上当前用户消息
        messages.append(HumanMessage(content=user_message))

        full_reply = ""
        async for chunk in stream_llm.astream(messages):
            token = chunk.content
            if token:
                full_reply += token
                yield token
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content=full_reply, msg_type="text")
