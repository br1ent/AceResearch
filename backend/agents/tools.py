"""Agent 工具：Tavily 搜索"""
from langchain_tavily import TavilySearch

from config.agents import get_agent_settings

settings = get_agent_settings()


def create_tavily_tool() -> TavilySearch:
    """创建 Tavily 搜索工具"""
    return TavilySearch(
        tavily_api_key=settings.TAVILY_API_KEY,
        max_results=settings.RESEARCHER_MAX_RESULTS,
    )
