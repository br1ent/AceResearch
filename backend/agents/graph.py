"""LangGraph 研究多 Agent 工作流（两阶段：规划 + 执行）"""
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
    return "rewrite"


def _make_initial_state(topic: str, user_id: int, conversation_id: int) -> ResearchState:
    return {
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


class PlanningWorkflow:
    """仅规划阶段：Planner → 返回大纲和子任务"""

    def __init__(self):
        builder = StateGraph(ResearchState)
        builder.add_node("planner", planner_node)
        builder.add_edge("planner", END)
        builder.set_entry_point("planner")
        self.compiled = builder.compile()

    async def run(self, topic: str, user_id: int, conversation_id: int) -> ResearchState:
        return await self.compiled.ainvoke(_make_initial_state(topic, user_id, conversation_id))


class ExecutionWorkflow:
    """执行阶段：从 Researchers 开始 → Analyst → Writer → Reviewer"""

    def __init__(self):
        builder = StateGraph(ResearchState)
        builder.add_node("researcher", researcher_node)
        builder.add_node("analyst", analyst_node)
        builder.add_node("writer", writer_node)
        builder.add_node("reviewer", reviewer_node)

        builder.add_edge("researcher", "analyst")
        builder.add_edge("analyst", "writer")
        builder.add_edge("writer", "reviewer")

        builder.add_conditional_edges("reviewer", should_review, {
            "rewrite": "writer",
            "end": END,
        })
        builder.set_entry_point("researcher")
        self.compiled = builder.compile()

    async def run(self, state: ResearchState) -> ResearchState:
        return await self.compiled.ainvoke(state)
