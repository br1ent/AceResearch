"""Agent 工具：时间、天气、搜索"""
from datetime import datetime, timezone, timedelta

import httpx
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from config.agents import get_agent_settings

settings = get_agent_settings()

# 中国时区 UTC+8
_CN_TZ = timezone(timedelta(hours=8))


@tool
def get_current_time() -> str:
    """获取当前中国时间（北京时间）。当用户询问时间、日期、今天几号等问题时使用。"""
    return datetime.now(_CN_TZ).strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。当用户询问某地天气、温度、是否下雨等问题时使用。

    Args:
        city: 城市名称，支持中文如"北京"，或 LocationID 如"101010100"
    """
    host = settings.QWEATHER_API_HOST
    api_key = settings.QWEATHER_API_KEY
    if not host or not api_key:
        return "天气查询失败：未配置和风天气 API Host 或 API Key"

    host = host.replace("https://", "").replace("http://", "").strip("/")

    try:
        # Step 1: GeoAPI 将城市名转为 LocationID
        geo_resp = httpx.get(
            f"https://{host}/geo/v2/city/lookup",
            params={"location": city, "key": api_key, "lang": "zh"},
            timeout=5.0,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if geo_data.get("code") != "200" or not geo_data.get("location"):
            return f"天气查询失败：找不到城市 '{city}'"

        location_id = geo_data["location"][0]["id"]
        normalized_city_name = geo_data["location"][0]["name"]

        # Step 2: 用 LocationID 查实时天气
        weather_resp = httpx.get(
            f"https://{host}/v7/weather/now",
            params={"location": location_id, "key": api_key, "lang": "zh"},
            timeout=5.0,
        )
        weather_resp.raise_for_status()
        data = weather_resp.json()

        if data.get("code") != "200":
            return f"天气查询失败：{data.get('code', '未知错误')}"

        now = data["now"]
        return (
            f"{normalized_city_name}天气：{now['text']}\n"
            f"温度：{now['temp']}°C（体感 {now['feelsLike']}°C）\n"
            f"风向：{now['windDir']} {now['windScale']}级\n"
            f"湿度：{now['humidity']}%\n"
            f"更新时间：{data['updateTime']}"
        )
    except Exception as e:
        return f"天气查询失败：{e}"


@tool
def web_search(query: str) -> str:
    """联网搜索获取最新信息。当用户询问新闻、实时信息、需要最新数据的问题时使用。

    Args:
        query: 搜索关键词
    """
    try:
        tool = TavilySearch(
            tavily_api_key=settings.TAVILY_API_KEY,
            max_results=3,
        )
        results = tool.invoke({"query": query})
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            url = r.get("url", "")
            content = r.get("content", "")[:300]
            lines.append(f"{i}. **{title}**\n   {url}\n   {content}")
        return "\n\n".join(lines) if lines else "未找到相关结果"
    except Exception as e:
        return f"搜索失败：{e}"


CHAT_TOOLS = [get_current_time, get_weather, web_search]

# 知识库模式额外工具（按需绑定）
@tool
def search_knowledge_base(query: str) -> str:
    """在用户上传的个人文档中搜索相关内容。当用户提问时，你必须优先使用这个工具来从文档中查找信息来回答。适用于任何用户提问，尤其是涉及文档内容的问题。

    Args:
        query: 搜索关键词或问题，用自然语言描述你想查找的内容
    """
    from services.knowledge_base.retrieval_service import search_knowledge
    from agents.chat.tools import _current_user_id
    return search_knowledge(_current_user_id, query)


_current_user_id: int = 0
KB_TOOLS = [search_knowledge_base]
