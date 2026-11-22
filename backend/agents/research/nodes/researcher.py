"""Researcher Agent：使用 Tavily 并行搜索每个子任务"""
import asyncio
import time
from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults

from config.agents import get_agent_settings
from agents.research.state import ResearchState, ResearchSubtask, SearchResultItem
from utils.telemetry import record
from utils.logger import logger

settings = get_agent_settings()

tavily = TavilySearchResults(
    tavily_api_key=settings.TAVILY_API_KEY,
    max_results=settings.RESEARCHER_MAX_RESULTS,
)

# 全局并发上限：限制同时发往 Tavily 的请求数（跨并发研究任务共享）
_sem = asyncio.Semaphore(settings.RESEARCHER_MAX_CONCURRENCY)


class InsufficientSourcesError(Exception):
    """可用来源不足：显式失败而非返回残缺报告。"""


async def _search_one(subtask: ResearchSubtask) -> List[SearchResultItem]:
    """搜索单个子任务：受全局 Semaphore 限流，单路超时/异常降级为空列表。"""
    async with _sem:
        start = time.perf_counter()
        try:
            results = await asyncio.wait_for(
                tavily.ainvoke({"query": subtask["description"]}),
                timeout=settings.RESEARCHER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            record("researcher_source", source=subtask["id"], status="timeout",
                   latency_ms=(time.perf_counter() - start) * 1000.0)
            return []
        except Exception as e:
            record("researcher_source", source=subtask["id"], status="error",
                   error=str(e)[:100], latency_ms=(time.perf_counter() - start) * 1000.0)
            return []

        latency_ms = (time.perf_counter() - start) * 1000.0
        if isinstance(results, str):
            record("researcher_source", source=subtask["id"], status="ok", n=1, latency_ms=latency_ms)
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
        record("researcher_source", source=subtask["id"], status="ok", n=len(items), latency_ms=latency_ms)
        return items


async def researcher_node(state: ResearchState) -> dict:
    """搜索节点：并行搜索所有子任务（限流 + 单路降级 + 兜底）。"""
    all_results: List[SearchResultItem] = []
    subtasks = state["subtasks"]

    start = time.perf_counter()
    results_list = await asyncio.gather(*(_search_one(s) for s in subtasks))
    latency_ms = (time.perf_counter() - start) * 1000.0

    for i, (subtask, results) in enumerate(zip(subtasks, results_list)):
        subtask["status"] = "completed" if results else "failed"
        all_results.extend(results)

    n_ok = sum(1 for r in results_list if r)
    record("researcher", latency_ms=latency_ms,
           n_results=len(all_results), n_subtasks=len(subtasks),
           failed_subtasks=len(subtasks) - n_ok)
    logger.info(
        "{} 完成 | {}s | {} 结果 / {} 子任务（{} 成功）",
        "researcher",
        round(latency_ms / 1000.0, 1),
        len(all_results),
        len(subtasks),
        n_ok,
        node="researcher",
        latency_ms=round(latency_ms, 3),
        n_results=len(all_results),
        n_subtasks=len(subtasks),
        n_ok=n_ok,
    )

    # 兜底：可用来源低于阈值时显式失败，避免把残缺结果交给下游
    if n_ok < settings.RESEARCHER_MIN_SOURCES:
        raise InsufficientSourcesError(
            f"仅 {n_ok}/{len(subtasks)} 路来源搜索成功，低于最小 {settings.RESEARCHER_MIN_SOURCES} 路，中止研究"
        )

    return {
        "search_results": all_results,
        "subtasks": subtasks,
        "status": "searching",
        "progress": 40.0,
    }
