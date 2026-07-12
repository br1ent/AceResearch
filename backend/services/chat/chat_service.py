"""闲聊服务：直接调用 DeepSeek 对话"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.agents import get_agent_settings
from config.prompts import get_chat_system_prompt
from services.chat import ConversationService

settings = get_agent_settings()

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=settings.DEEPSEEK_TEMPERATURE,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS,
)


class ChatService:
    """简单的闲聊对话服务"""

    def __init__(self, db_session):
        self.conv_service = ConversationService(db_session)
        self.db = db_session

    async def chat(self, conversation_id: int, user_message: str) -> str:
        """执行一次对话：保存用户消息 → 调 LLM → 保存回复"""
        # 1. 保存用户消息
        self.conv_service.add_message(
            conv_id=conversation_id,
            role="user",
            content=user_message,
            msg_type="text",
        )

        # 2. 获取历史消息（最近 20 条作为上下文）
        history = self.conv_service.get_messages(conversation_id, limit=20)

        # 3. 从数据库读取系统提示词
        system_prompt = get_chat_system_prompt()
        messages = [SystemMessage(content=system_prompt)]
        for msg in history[:-1]:  # 排除刚加的这条
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # 4. 调用 DeepSeek
        response = await llm.ainvoke(messages)
        reply = response.content

        # 5. 更新对话标题（首条消息后自动生成简短标题）
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv:
            msgs_count = len(history)
            if msgs_count <= 2:
                short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                self.conv_service.update_title(conversation_id, short_title)

        # 6. 保存回复
        self.conv_service.add_message(
            conv_id=conversation_id,
            role="assistant",
            content=reply,
            msg_type="text",
        )

        return reply

    async def chat_stream(self, conversation_id: int, user_message: str):
        """流式对话：逐 token 返回 LLM 输出"""
        # 1. 保存用户消息
        self.conv_service.add_message(
            conv_id=conversation_id,
            role="user",
            content=user_message,
            msg_type="text",
        )

        # 2. 获取历史消息
        history = self.conv_service.get_messages(conversation_id, limit=20)

        # 3. 构建消息列表
        system_prompt = get_chat_system_prompt()
        messages = [SystemMessage(content=system_prompt)]
        for msg in history[:-1]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # 4. 流式调用 DeepSeek
        full_reply = ""
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_reply += token
                yield token

        # 5. 更新标题
        from models.chat import Conversation as ConvModel
        conv = self.db.query(ConvModel).filter(ConvModel.id == conversation_id).first()
        if conv and len(history) <= 2:
            short_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
            self.conv_service.update_title(conversation_id, short_title)

        # 6. 保存完整回复
        self.conv_service.add_message(
            conv_id=conversation_id,
            role="assistant",
            content=full_reply,
            msg_type="text",
        )
