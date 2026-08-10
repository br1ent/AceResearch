from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """AI Agent 配置，从 .env 读取"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # DeepSeek (OpenAI 兼容接口)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_TEMPERATURE: float = 0.7
    DEEPSEEK_MAX_TOKENS: int = 8192

    # Tavily 搜索
    TAVILY_API_KEY: str = ""

    # 和风天气 (Console V4)
    QWEATHER_API_HOST: str = ""
    QWEATHER_API_KEY: str = ""

    # Agent 行为控制
    PLANNER_TEMPERATURE: float = 0.5
    RESEARCHER_MAX_RESULTS: int = 5
    WRITER_TEMPERATURE: float = 0.6
    REVIEWER_MAX_RETRIES: int = 2
    REVIEWER_PASS_THRESHOLD: float = 5.0  # 平均分 >= 此值即使 LLM 判 false 也放行（0 禁用）
    CHAT_MAX_ITERATIONS: int = 5


@lru_cache
def get_agent_settings() -> AgentSettings:
    """获取 Agent 配置单例"""
    return AgentSettings()
