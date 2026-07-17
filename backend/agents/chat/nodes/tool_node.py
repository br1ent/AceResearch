"""闲聊工具执行节点：解析 tool_calls 并执行对应工具"""
from langchain_core.messages import ToolMessage

from agents.chat.state import ChatState
from agents.chat.tools import CHAT_TOOLS, KB_TOOLS


# 工具名 → 工具函数的映射
_tool_map = {t.name: t for t in CHAT_TOOLS + KB_TOOLS}


def tool_node(state: ChatState) -> dict:
    """执行 LLM 返回的 tool_calls，返回 ToolMessage 列表"""
    last_msg = state["messages"][-1]
    tool_messages = []

    for tool_call in last_msg.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"]

        try:
            if name in _tool_map:
                result = _tool_map[name].invoke(args)
            else:
                result = f"未知工具：{name}"
        except Exception as e:
            result = f"工具执行错误：{e}"

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call_id))

    return {
        "messages": tool_messages,
        "iteration": state["iteration"] + 1,
    }
