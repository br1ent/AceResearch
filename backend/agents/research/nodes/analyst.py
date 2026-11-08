"""Analyst Agent：汇总分析所有搜索结果"""
from langchain_core.prompts import ChatPromptTemplate

from config.agents import get_agent_settings
from config.prompts import get_research_prompt
from agents.research.state import ResearchState
from utils.user_llm import get_chat_llm

settings = get_agent_settings()


async def analyst_node(state: ResearchState) -> dict:
    """分析节点：综合搜索结果"""
    materials = []
    for i, r in enumerate(state["search_results"], 1):
        materials.append(f"[来源 {i}] 标题：{r['title']}\nURL：{r['url']}\n内容：{r['content']}\n")
    search_materials = "\n---\n".join(materials[:50])

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_research_prompt("analyst")),
        ("human", "研究主题：{topic}\n\n搜索材料：\n{search_materials}"),
    ])

    chain = prompt | get_chat_llm(
        state["user_id"],
        temperature=settings.DEEPSEEK_TEMPERATURE,
        max_tokens=settings.DEEPSEEK_MAX_TOKENS,
    )
    response = await chain.ainvoke({
        "topic": state["topic"],
        "search_materials": search_materials or "（无搜索结果）",
    })

    return {
        "analysis": response.content,
        "status": "analyzing",
        "progress": 60.0,
    }
