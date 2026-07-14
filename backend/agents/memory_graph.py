"""记忆 LangGraph：START → extract_memory → END"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from agents.nodes.memory_node import extract_memory_node


class MemoryState(TypedDict):
    user_id: int
    dialogue: str          # 最近的对话文本
    existing_memory: str   # 用户已有的 memory 字段
    memory_updated: bool   # 是否更新了记忆
    memory_summary: str    # 更新后的记忆文本


class MemoryGraph:
    """最简记忆图：一个节点完成提取和更新"""

    def __init__(self):
        builder = StateGraph(MemoryState)
        builder.add_node("extract_memory", extract_memory_node)
        builder.add_edge("extract_memory", END)
        builder.set_entry_point("extract_memory")
        self.compiled = builder.compile()

    def invoke(self, state: MemoryState) -> MemoryState:
        return self.compiled.invoke(state)

    async def ainvoke(self, state: MemoryState) -> MemoryState:
        return await self.compiled.ainvoke(state)
