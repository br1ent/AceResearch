"""Reviewer Agent：审查报告质量，决定是否通过或需要修改"""
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.agents import get_agent_settings
from config.prompts import get_research_prompt
from agents.state import ResearchState

settings = get_agent_settings()

llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=settings.DEEPSEEK_TEMPERATURE,
    max_tokens=settings.DEEPSEEK_MAX_TOKENS,
)


def reviewer_node(state: ResearchState) -> dict:
    """审查节点：评估报告质量"""
    if not state.get("report_draft"):
        return {"final_report": "报告生成失败", "status": "failed", "error": "报告草稿为空"}

    outline_text = "\n".join(f"- {s}" for s in state["outline"])

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_research_prompt("reviewer")),
        (
            "human",
            "报告标题：{title}\n\n大纲：\n{outline}\n\n报告内容：\n{report}",
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "title": state["report_title"],
        "outline": outline_text,
        "report": state["report_draft"][:8000],
    })

    text = response.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        review = json.loads(text)
    except json.JSONDecodeError:
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
        }

    retries = state.get("reviewer_retries", 0)

    if review.get("passed", False):
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
        }
    elif retries < settings.REVIEWER_MAX_RETRIES:
        return {
            "reviewer_retries": retries + 1,
            "status": "reviewing",
            "progress": 85.0,
        }
    else:
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
        }
