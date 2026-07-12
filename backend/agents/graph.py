"""LangGraph 研究多 Agent 工作流"""
from langgraph.graph import StateGraph, END

from agents.state import ResearchState
from agents.nodes.planner import planner_node
from agents.nodes.researcher import researcher_node
from agents.nodes.analyst import analyst_node
from agents.nodes.writer import writer_node
from agents.nodes.reviewer import reviewer_node


def should_review(state: ResearchState) -> str:
    """审查后的路由决策"""
    if state["status"] == "completed" or state["status"] == "failed":
        return "end"
    # status 为 "reviewing" 表示需要回到 writer 修改
    return "rewrite"


class ResearchWorkflow:
    """研究多 Agent 工作流"""

    def __init__(self):
        self.graph = self._build_graph()
        self.compiled = self.graph.compile()

    @staticmethod
    def _build_graph() -> StateGraph:
        """构建 LangGraph 图"""
        builder = StateGraph(ResearchState)

        # 注册节点
        builder.add_node("planner", planner_node)
        builder.add_node("researcher", researcher_node)
        builder.add_node("analyst", analyst_node)
        builder.add_node("writer", writer_node)
        builder.add_node("reviewer", reviewer_node)

        # 顺序边
        builder.add_edge("planner", "researcher")
        builder.add_edge("researcher", "analyst")
        builder.add_edge("analyst", "writer")
        builder.add_edge("writer", "reviewer")

        # 条件边：reviewer → writer（修改）或 END
        builder.add_conditional_edges(
            "reviewer",
            should_review,
            {
                "rewrite": "writer",   # 回 writer 修改
                "end": END,            # 结束
            },
        )

        # 入口
        builder.set_entry_point("planner")

        return builder

    async def run(
        self,
        topic: str,
        user_id: int,
        conversation_id: int,
    ) -> ResearchState:
        """执行一次研究工作流"""
        initial_state: ResearchState = {
            "topic": topic,
            "user_id": user_id,
            "conversation_id": conversation_id,

            "outline": [],
            "subtasks": [],

            "search_results": [],

            "analysis": "",

            "report_title": "",
            "report_draft": "",
            "final_report": "",
            "sources": [],

            "status": "running",
            "progress": 0.0,
            "error": None,
            "reviewer_retries": 0,
        }

        result = await self.compiled.ainvoke(initial_state)
        return result
