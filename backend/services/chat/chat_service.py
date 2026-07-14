"""闲聊服务：使用 LangGraph ChatGraph 调用 DeepSeek + 长期记忆"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.agents import get_agent_settings
from config.prompts import get_chat_system_prompt
from agents.chat_graph import ChatGraph

settings = get_agent_settings()

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
        self.db = db_session
        from services.chat.conversation_service import ConversationService
        self.conv_service = ConversationService(db_session)

    def _get_user_memory(self, user_id: int) -> str:
        """从 users.memory 读取用户记忆"""
        from models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.memory if user and user.memory else ""

    def _update_user_memory(self, user_id: int, summary: str):
        """写入 users.memory"""
        from models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.memory = summary
            self.db.commit()

    async def _run_memory_extraction(self, conversation_id: int, user_id: int):
        """后台运行记忆提取（每 10 条触发）"""
        from agents.memory_graph import MemoryGraph
        mg = MemoryGraph()

        history = self.conv_service.get_messages(conversation_id, user_id=user_id, limit=20)
        if len(history) < 10 or len(history) % 10 != 0:
            return

        dialogue = "\n".join(
            f"{'用户' if m.role == 'user' else '助手'}: {m.content[:200]}"
            for m in history[-10:]
        )
        existing = self._get_user_memory(user_id)

        result = mg.invoke({
            "user_id": user_id,
            "dialogue": dialogue,
            "existing_memory": existing,
            "memory_updated": False,
            "memory_summary": existing,
        })
        if result.get("memory_updated"):
            self._update_user_memory(user_id, result["memory_summary"])

    async def chat(self, conversation_id: int, user_message: str) -> str:
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=user_message, msg_type="text")
        history = self.conv_service.get_messages(conversation_id, limit=20)
        uid = self._get_current_user_id(conversation_id)

        hist_list = [{"role": m.role, "content": m.content} for m in history[:-1]]
        result = await chat_graph.ainvoke({
            "conversation_id": conversation_id, "user_message": user_message,
            "history": hist_list, "reply": "",
        })
        reply = result["reply"]

        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content=reply, msg_type="text")
        if uid:
            asyncio.create_task(self._run_memory_extraction(conversation_id, uid))
        return reply

    def _get_current_user_id(self, conversation_id: int) -> int:
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        return conv.user_id if conv else 0

    async def chat_stream(self, conversation_id: int, user_message: str):
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=user_message, msg_type="text")
        history = self.conv_service.get_messages(conversation_id, limit=20)
        uid = self._get_current_user_id(conversation_id)

        memory_text = self._get_user_memory(uid) if uid else ""

        system_prompt = get_chat_system_prompt()
        messages = [SystemMessage(content=system_prompt)]
        if memory_text:
            messages.append(SystemMessage(content=f"[用户画像]\n{memory_text}"))
        for msg in history[:-1]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=user_message))

        full_reply = ""
        async for chunk in stream_llm.astream(messages):
            text = chunk.content
            if text:
                full_reply += text
                yield text

        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content=full_reply, msg_type="text")

        if uid:
            asyncio.create_task(self._run_memory_extraction(conversation_id, uid))
