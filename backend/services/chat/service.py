"""闲聊 / 知识检索服务：LangGraph 上下文组装 + ReAct 工具循环 + DeepSeek 流式输出"""
import asyncio
from langchain_openai import ChatOpenAI

from config.agents import get_agent_settings
from agents.chat.graph import ChatGraph
from agents.chat.state import ChatState
from agents.chat.tools import CHAT_TOOLS, KB_TOOLS
from agents.chat.nodes.tool_node import tool_node

settings = get_agent_settings()

_llm = ChatOpenAI(
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
        from services.chat.conversation import ConversationService
        self.conv_service = ConversationService(db_session)

    def _get_user_memory(self, user_id: int, mode: str = "chat") -> str:
        from models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return ""
        return user.kb_memory if mode == "knowledge" else user.memory

    def _update_user_memory(self, user_id: int, summary: str, mode: str = "chat"):
        from models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            if mode == "knowledge":
                user.kb_memory = summary
            else:
                user.memory = summary
            self.db.commit()

    async def _run_memory_extraction(self, conversation_id: int, user_id: int, mode: str = "chat"):
        from agents.memory.graph import MemoryGraph
        mg = MemoryGraph()

        history = self.conv_service.get_messages(conversation_id, user_id=user_id, limit=20)
        if len(history) < 10 or len(history) % 10 != 0:
            return

        dialogue = "\n".join(
            f"{'用户' if m.role == 'user' else '助手'}: {m.content[:200]}"
            for m in history[-10:]
        )
        existing = self._get_user_memory(user_id, mode)

        result = mg.invoke({
            "user_id": user_id,
            "dialogue": dialogue,
            "existing_memory": existing,
            "memory_updated": False,
            "memory_summary": existing,
        })
        if result.get("memory_updated"):
            self._update_user_memory(user_id, result["memory_summary"], mode)

    def _get_current_user_id(self, conversation_id: int) -> int:
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        return conv.user_id if conv else 0

    async def chat_stream(self, conversation_id: int, user_message: str, mode: str = "chat"):
        self.conv_service.add_message(conv_id=conversation_id, role="user", content=user_message, msg_type="text")
        uid = self._get_current_user_id(conversation_id)

        # 知识库模式绑定额外工具
        tools = CHAT_TOOLS
        if mode == "knowledge":
            import agents.chat.tools as tools_mod
            tools_mod._current_user_id = uid
            tools = CHAT_TOOLS + KB_TOOLS

        # 1. 通过 LangGraph 组装上下文
        state: ChatState = chat_graph.invoke({
            "conversation_id": conversation_id,
            "user_message": user_message,
            "user_id": uid,
            "mode": mode,
            "system_prompt": "",
            "memory_text": "",
            "history": [],
            "messages": [],
            "iteration": 0,
            "max_iterations": settings.CHAT_MAX_ITERATIONS,
        })
        messages = state["messages"]
        history = state["history"]

        # 2. ReAct 循环：LLM 流式调用 + 工具执行
        llm_with_tools = _llm.bind_tools(tools)
        full_reply = ""

        while True:
            full_msg = None
            buffered_chunks = []
            saw_tool_call = False

            async for chunk in llm_with_tools.astream(messages):
                buffered_chunks.append(chunk)
                if chunk.tool_call_chunks:
                    saw_tool_call = True
                elif chunk.content and not saw_tool_call:
                    full_reply += chunk.content
                    yield chunk.content

            if buffered_chunks:
                full_msg = buffered_chunks[0]
                for c in buffered_chunks[1:]:
                    full_msg += c

            if full_msg is None:
                break

            messages.append(full_msg)

            # 没有 tool_calls → 最终回复完成
            if not saw_tool_call and not (hasattr(full_msg, 'tool_calls') and full_msg.tool_calls):
                break

            # 有 tool_calls → 执行工具
            tool_state = tool_node({
                **state,
                "messages": messages,
                "iteration": state["iteration"],
            })
            messages.extend(tool_state["messages"])
            state["iteration"] = tool_state["iteration"]

            # 超过最大轮次 → 强制结束
            if state["iteration"] >= state["max_iterations"]:
                break

        # 兜底：如果没产出内容
        if not full_reply and messages:
            last = messages[-1]
            if hasattr(last, "content"):
                full_reply = last.content
                yield full_reply

        # 3. 保存回复
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        self.conv_service.add_message(conv_id=conversation_id, role="assistant", content=full_reply, msg_type="text")

        if uid:
            asyncio.create_task(self._run_memory_extraction(conversation_id, uid, mode))
