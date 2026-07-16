"""Planner Agent：分析研究主题，生成大纲和子任务"""
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.agents import get_agent_settings
from config.prompts import get_research_prompt
from agents.research.state import ResearchState, ResearchSubtask

settings = get_agent_settings()

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=settings.PLANNER_TEMPERATURE,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS,
)


async def planner_node(state: ResearchState) -> dict:
    """规划节点：生成大纲和子任务"""
    system_prompt = get_research_prompt("planner")
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "研究主题：{topic}"),
    ])

    chain = prompt | llm
    response = await chain.ainvoke({"topic": state["topic"]})

    text = response.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    parsed = json.loads(text)

    subtasks = [
        ResearchSubtask(id=s["id"], title=s["title"], description=s["description"], status="pending")
        for s in parsed["subtasks"]
    ]

    return {
        "outline": parsed["outline"],
        "subtasks": subtasks,
        "report_title": parsed["title"],
        "status": "planning",
        "progress": 10.0,
    }
