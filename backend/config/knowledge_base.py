from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class KnowledgeBaseSettings(BaseSettings):
    """知识库配置，从 .env 读取"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 嵌入模型（阿里云百炼）
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_MODEL: str = "text-embedding-v4"

    # 重排序模型（阿里云百炼）
    RERANK_WORKSPACE_ID: str = ""
    RERANK_MODEL: str = "qwen3-rerank"
    RERANK_TOP_N: int = 3

    CHROMA_PERSIST_DIR: str = "chroma_data"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    MAX_DOCUMENTS_PER_USER: int = 3
    MAX_FILE_SIZE_MB: int = 5
    MAX_TEXT_LENGTH: int = 1000


@lru_cache
def get_kb_settings() -> KnowledgeBaseSettings:
    return KnowledgeBaseSettings()
