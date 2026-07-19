"""研究完成后 LLM 自动生成总结"""
from langchain_openai import ChatOpenAI

from config.agents import get_agent_settings
from config.prompts import get_summarizer_prompt

settings = get_agent_settings()

_llm = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    model=settings.DEEPSEEK_MODEL,
    temperature=0.3,
    max_tokens=512,
)


async def summarize_report(title: str, outline: list, content: str) -> str:
    """让 LLM 自动总结本次研究做了什么、写了什么"""
    outline_text = "\n".join(f"- {o}" for o in outline)
    system_prompt = get_summarizer_prompt()
    prompt = (
        f"{system_prompt}\n\n"
        f"报告标题：{title}\n\n"
        f"大纲：\n{outline_text}\n\n"
        f"报告内容（摘要）：{content[:2000]}"
    )
    try:
        response = await _llm.ainvoke(prompt)
        return response.content.strip()
    except Exception:
        return (
            f"📄 研究报告已生成\n\n"
            f"标题：{title}\n"
            f"本次研究已全部完成，报告已保存到「我的报告」页面。"
        )
