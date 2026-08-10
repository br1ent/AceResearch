"""Reviewer Agent：审查报告质量，决定是否通过或需要修改"""
import json
import re
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.agents import get_agent_settings
from config.prompts import get_research_prompt
from agents.research.state import ResearchState
from utils.logger import review_logger

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


async def _extract_json(text: str) -> dict | None:
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
        resp = await _fix_llm.ainvoke([
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


async def reviewer_node(state: ResearchState) -> dict:
    """审查节点：评估报告质量"""
    report_title = state.get("report_title", "未知标题")
    retries = state.get("reviewer_retries", 0)

    if not state.get("report_draft"):
        review_logger.error("报告草稿为空，无法审查 | 标题: {}", report_title)
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
    response = await chain.ainvoke({
        "title": report_title,
        "outline": outline_text,
        "report": state["report_draft"][:8000],
    })

    review = await _extract_json(response.content)

    # 解析失败 → 强制触发重写
    if review is None:
        review_logger.warning(
            "第 {} 次审查 | JSON 解析失败 | 标题: {} | 原始输出前200字: {}",
            retries + 1, report_title, response.content[:200],
        )
        if retries < settings.REVIEWER_MAX_RETRIES:
            history = list(state.get("review_history", []))
            history.append({
                "attempt": retries + 1,
                "passed": False,
                "score": None,
                "issues": ["JSON 解析失败"],
                "suggestions": "请重新生成格式规范的报告",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {
                "reviewer_retries": retries + 1,
                "status": "reviewing",
                "progress": 85.0,
                "review_score": None,
                "review_history": history,
                "reviewer_feedback": "JSON 解析失败，请重新生成格式规范的报告",
            }
        else:
            review_logger.warning("重试耗尽 ({}次)，放行报告 | 标题: {}", retries + 1, report_title)
            return {
                "final_report": state["report_draft"],
                "status": "completed",
                "progress": 100.0,
            }

    passed = review.get("passed", False)

    # 评分：优先从 scores 字典取平均值，否则取 score 字段
    scores_dict = review.get("scores")
    if isinstance(scores_dict, dict) and scores_dict:
        score = round(sum(scores_dict.values()) / len(scores_dict), 1)
    else:
        score = review.get("score")

    # 问题列表：prompt 可能用 improvements 或 issues
    issues = review.get("improvements") or review.get("issues") or []
    if not isinstance(issues, list):
        issues = [str(issues)]

    # 建议/总结：prompt 可能用 summary 或 suggestions
    suggestions = review.get("summary") or review.get("suggestions") or ""

    history = list(state.get("review_history", []))
    history.append({
        "attempt": retries + 1,
        "passed": passed,
        "score": score,
        "scores": scores_dict if isinstance(scores_dict, dict) else None,
        "issues": issues,
        "suggestions": suggestions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # 阈值覆盖：分数达标但 LLM 判不通过时，强制放行
    threshold = settings.REVIEWER_PASS_THRESHOLD
    if not passed and score is not None and threshold > 0 and score >= threshold:
        passed = True
        review_logger.info(
            "第 {} 次审查 | LLM 判未通过 但分数 {} >= 阈值 {}，覆盖为通过 | 标题: {}",
            retries + 1, score, threshold, report_title,
        )

    if passed:
        subs = f" 子项: {scores_dict}" if isinstance(scores_dict, dict) else ""
        sug = f" | 评价: {suggestions}" if suggestions else ""
        review_logger.info(
            "第 {} 次审查 | 通过 | 分数: {} |{}{} 标题: {}",
            retries + 1, score, subs, sug, report_title,
        )
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
            "review_score": score,
            "review_history": history,
        }

    # 未通过
    feedback_text = "问题列表：\n" + "\n".join(f"- {i}" for i in issues)
    if suggestions:
        feedback_text += f"\n\n改进建议：{suggestions}"

    if retries < settings.REVIEWER_MAX_RETRIES:
        subs = f" 子项: {scores_dict}" if isinstance(scores_dict, dict) else ""
        review_logger.warning(
            "第 {} 次审查 | 未通过 | 分数: {} |{} 问题数: {} | 触发第 {} 次重写 | 标题: {}",
            retries + 1, score, subs, len(issues), retries + 1, report_title,
        )
        review_logger.debug("审查反馈: {}", feedback_text[:300])
        return {
            "reviewer_retries": retries + 1,
            "status": "reviewing",
            "progress": 85.0,
            "review_score": score,
            "review_history": history,
            "reviewer_feedback": feedback_text,
        }
    else:
        review_logger.warning(
            "第 {} 次审查 | 未通过 (重试耗尽，放行) | 分数: {} | 问题数: {} | 标题: {}",
            retries + 1, score, len(issues), report_title,
        )
        return {
            "final_report": state["report_draft"],
            "status": "completed",
            "progress": 100.0,
            "review_score": score,
            "review_history": history,
        }
