"""闲聊模式 LangGraph 状态定义"""
from typing import TypedDict, List
from langchain_core.messages import BaseMessage


class ChatState(TypedDict):
    """闲聊图的共享状态"""
    conversation_id: int
    user_message: str
    user_id: int
    mode: str  # chat / knowledge
    # 上下文组件
    system_prompt: str
    memory_text: str
    history: List[dict]
    # 组装后的完整消息列表（含 ToolMessage）
    messages: List[BaseMessage]
    # 工具调用控制
    iteration: int
    max_iterations: int
