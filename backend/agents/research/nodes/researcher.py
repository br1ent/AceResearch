"""Researcher Agent：使用 Tavily 并行搜索每个子任务"""
import asyncio
import time
from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults

from config.agents import get_agent_settings
from agents.research.state import ResearchState, ResearchSubtask, SearchResultItem
from utils.telemetry import record

settings = get_agent_settings()

tavily = TavilySearchResults(
    tavily_api_key=settings.TAVILY_API_KEY,
    max_results=settings.RESEARCHER_MAX_RESULTS,
)


async def _search_one(subtask: ResearchSubtask) -> List[SearchResultItem]:
    """搜索单个子任务"""
    try:
        results = await asyncio.wait_for(
            tavily.ainvoke({"query": subtask["description"]}),
            timeout=30.0,
        )
        if isinstance(results, str):
            return [SearchResultItem(title=subtask["description"], url="", content=results[:500], score=0.0)]
        items = []
        for r in results:
            if isinstance(r, dict):
                items.append(SearchResultItem(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                ))
            else:
                items.append(SearchResultItem(
                    title=str(r)[:100],
                    url="",
                    content=str(r)[:500],
                    score=0.0,
                ))
        return items
    except asyncio.TimeoutError:
        return []
    except Exception:
        return []


async def researcher_node(state: ResearchState) -> dict:
    """搜索节点：并行搜索所有子任务"""
    all_results: List[SearchResultItem] = []
    subtasks = state["subtasks"]

    start = time.perf_counter()
    tasks = [_search_one(s) for s in subtasks]
    results_list = await asyncio.gather(*tasks)
    latency_ms = (time.perf_counter() - start) * 1000.0

    for i, (subtask, results) in enumerate(zip(subtasks, results_list)):
        subtask["status"] = "completed" if results else "failed"
        all_results.extend(results)

    record("researcher", latency_ms=latency_ms,
           n_results=len(all_results), n_subtasks=len(subtasks),
           failed_subtasks=sum(1 for s in subtasks if s["status"] == "failed"))

    return {
        "search_results": all_results,
        "subtasks": subtasks,
        "status": "searching",
        "progress": 40.0,
    }
