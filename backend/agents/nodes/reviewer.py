"""Reviewer Agent：审查报告质量，决定是否通过或需要修改"""
import json
import re

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
    temperature=0.0,
    max_tokens=1024,
)

_fix_llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=0.0,
    max_tokens=1024,
)


def _extract_json(text: str) -> dict | None:
    """分层提取 JSON：先尝试直接解析，再用正则匹配，最后用 LLM 修复"""
    # 第一层：直接解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 第二层：去掉 markdown 代码块
    cleaned = text
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 第三层：正则提取第一个 { } 或 [ ] 块
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        match = re.search(pattern, cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    # 第四层：用 LLM 修复
    try:
        resp = _fix_llm.invoke([
            ("system", "你是一个 JSON 修复器。提取下面文本中的 JSON 对象（包含 passed、issues、suggestions 字段），只输出 JSON，不要其他内容。"),
            ("human", text[:2000]),
        ])
        fixed = resp.content.strip()
        if fixed.startswith("```"):
            fixed = fixed.split("\n", 1)[1] if "\n" in fixed else fixed[3:]
            fixed = fixed.rsplit("```", 1)[0]
        return json.loads(fixed.strip())
    except (json.JSONDecodeError, Exception):
        pass

    return None


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

    review = _extract_json(response.content)

    # 解析失败或 LLM 无法修复 → 强制触发重写
    if review is None:
        retries = state.get("reviewer_retries", 0)
        if retries < settings.REVIEWER_MAX_RETRIES:
            return {
                "reviewer_retries": retries + 1,
                "status": "reviewing",
                "progress": 85.0,
                "reviewer_feedback": "JSON 解析失败，请重新生成格式规范的报告",
            }
        else:
            # 重试耗尽，只能放行
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
        # 把审查建议传给 Writer
        issues = review.get("issues", [])
        suggestions = review.get("suggestions", "")
        if isinstance(issues, list):
            feedback_text = "问题列表：\n" + "\n".join(f"- {i}" for i in issues)
        else:
            feedback_text = f"问题：{issues}"
        if suggestions:
            feedback_text += f"\n\n改进建议：{suggestions}"

        return {
            "reviewer_retries": retries + 1,
            "status": "reviewing",
            "progress": 85.0,
            "reviewer_feedback": feedback_text,
        }
    else:
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
        }
