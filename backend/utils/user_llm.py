"""按用户解析有效 API Key，并构建带缓存的 LLM / Embedding 客户端。

用户必须在个人资料中配置自己的 API Key，未配置的功能不可用（不回退全局 key）。
"""
import httpx
from fastapi import HTTPException
from langchain_openai import ChatOpenAI

from config.agents import get_agent_settings
from config.database import SessionLocal
from config.knowledge_base import get_kb_settings

_key_cache: dict[int, tuple[str, str, str]] = {}
_llm_cache: dict[tuple, ChatOpenAI] = {}
_embedding_cache: dict[int, "DashScopeEmbedding"] = {}


class DashScopeEmbedding:
    def __init__(self, api_key: str):
        kb_settings = get_kb_settings()
        self.api_key = api_key
        self.base_url = kb_settings.EMBEDDING_BASE_URL.rstrip("/")
        self.model = kb_settings.EMBEDDING_MODEL

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            json={"model": self.model, "input": texts},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )
        data = resp.json()
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API error: {data}")
        items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in items]


def get_effective_keys(user_id: int | None) -> tuple[str, str, str]:
    """返回用户自己配置的 (deepseek_key, dashscope_key, workspace_id)，未配置为空字符串"""
    if not user_id:
        return ("", "", "")
    if user_id in _key_cache:
        return _key_cache[user_id]

    from models.user import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

    keys = (
        (user.deepseek_api_key or "") if user else "",
        (user.dashscope_api_key or "") if user else "",
        (user.dashscope_workspace_id or "") if user else "",
    )
    _key_cache[user_id] = keys
    return keys


def require_deepseek_key(user_id: int) -> str:
    """校验用户已配置 DeepSeek Key，未配置则 400"""
    key = get_effective_keys(user_id)[0]
    if not key:
        raise HTTPException(status_code=400, detail="请先在「个人资料 - 模型 API 配置」中配置 DeepSeek API Key 后再使用")
    return key


def require_dashscope_key(user_id: int) -> str:
    """校验用户已配置百炼 Key，未配置则 400"""
    key = get_effective_keys(user_id)[1]
    if not key:
        raise HTTPException(status_code=400, detail="请先在「个人资料 - 模型 API 配置」中配置阿里云百炼 API Key 后再使用")
    return key


def get_chat_llm(user_id: int | None, *, temperature: float, max_tokens: int) -> ChatOpenAI:
    """按用户构建 ChatOpenAI 客户端（带缓存，key 变更后自动重建）"""
    agent_settings = get_agent_settings()
    api_key = get_effective_keys(user_id)[0]
    cache_key = (user_id or 0, api_key, temperature, max_tokens)
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = ChatOpenAI(
            api_key=api_key,
            base_url=agent_settings.DEEPSEEK_BASE_URL,
            model=agent_settings.DEEPSEEK_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _llm_cache[cache_key]


def get_embeddings(user_id: int | None) -> DashScopeEmbedding:
    """按用户构建 Embedding 客户端（带缓存）"""
    api_key = get_effective_keys(user_id)[1]
    cache_key = user_id or 0
    cached = _embedding_cache.get(cache_key)
    if cached is None or cached.api_key != api_key:
        cached = DashScopeEmbedding(api_key)
        _embedding_cache[cache_key] = cached
    return cached


def invalidate_user_llm(user_id: int) -> None:
    """用户更新 API Key 后清除其缓存"""
    _key_cache.pop(user_id, None)
    _embedding_cache.pop(user_id, None)
    for cache_key in [k for k in _llm_cache if k[0] == user_id]:
        _llm_cache.pop(cache_key, None)
