"""Researcher Agent：使用 Tavily 并行搜索每个子任务"""
import asyncio
from typing import List

from langchain_tavily import TavilySearch

from config.agents import get_agent_settings
from agents.state import ResearchState, ResearchSubtask, SearchResultItem

settings = get_agent_settings()

tavily = TavilySearch(
    tavily_api_key=settings.TAVILY_API_KEY,
    max_results=settings.RESEARCHER_MAX_RESULTS,
)


async def _search_one(subtask: ResearchSubtask) -> List[SearchResultItem]:
    """搜索单个子任务"""
    try:
        results = await tavily.ainvoke({"query": subtask["description"]})
        items = []
        for r in results:
            items.append(SearchResultItem(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
            ))
        return items
    except Exception:
        return []


async def researcher_node(state: ResearchState) -> dict:
    """搜索节点：并行搜索所有子任务（async，支持 LangGraph ainvoke）"""
    all_results: List[SearchResultItem] = []
    subtasks = state["subtasks"]

    # 并行搜索
    tasks = [_search_one(s) for s in subtasks]
    results_list = await asyncio.gather(*tasks)

    for i, (subtask, results) in enumerate(zip(subtasks, results_list)):
        subtask["status"] = "completed" if results else "failed"
        all_results.extend(results)

    return {
        "search_results": all_results,
        "subtasks": subtasks,
        "status": "searching",
        "progress": 40.0,
    }
