"""Writer Agent：根据大纲和分析结果撰写研究报告"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.agents import get_agent_settings
from config.prompts import get_research_prompt
from agents.state import ResearchState, SourceItem

settings = get_agent_settings()

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=settings.WRITER_TEMPERATURE,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS * 2,
)


def writer_node(state: ResearchState) -> dict:
    """写作节点：撰写研究报告"""
    outline_text = "\n".join(f"- {s}" for s in state["outline"])

    materials = []
    for i, r in enumerate(state["search_results"], 1):
        materials.append(f"[来源 {i}] 标题：{r['title']}\nURL：{r['url']}\n摘要：{r['content'][:300]}\n")
    search_materials = "\n---\n".join(materials[:50])

    # 如果有审查反馈，加入改写提示
    reviewer_feedback = state.get("reviewer_feedback", "")
    feedback_section = ""
    if reviewer_feedback:
        feedback_section = f"\n\n上次审查意见（请针对这些问题进行修改）：\n{reviewer_feedback}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_research_prompt("writer")),
        (
            "human",
            "报告标题：{title}\n\n大纲结构：\n{outline}\n\n综合分析：\n{analysis}\n\n搜索材料：\n{search_materials}{feedback_section}",
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "title": state["report_title"],
        "outline": outline_text,
        "analysis": state["analysis"],
        "search_materials": search_materials or "（无搜索结果）",
        "feedback_section": feedback_section,
    })

    sources = [
        SourceItem(index=i + 1, title=r["title"], url=r["url"], snippet=r["content"][:200])
        for i, r in enumerate(state["search_results"])
    ]

    return {
        "report_draft": response.content,
        "sources": sources,
        "status": "writing",
        "progress": 80.0,
    }
