"""轻量基准埋点：默认关闭，仅当 benchmark runner 调用 enable() 后才记录。

设计目标：
- 对生产零影响：关闭时所有函数都是 no-op，开销可忽略。
- 一次采集全部基线指标：每节点时延、token 用量、搜索耗时。

用法（runner）：
    import utils.telemetry as telemetry
    telemetry.enable()
    ... 运行流水线 ...
    rows = telemetry.records()
    telemetry.disable()
"""
from __future__ import annotations

import threading
import time
from typing import Any, Awaitable


class _Collector:
    def __init__(self) -> None:
        self._enabled = False
        self._records: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def enable(self) -> None:
        with self._lock:
            self._enabled = True
            self._records = []

    def disable(self) -> None:
        with self._lock:
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def add(self, record: dict[str, Any]) -> None:
        if not self._enabled:
            return
        with self._lock:
            self._records.append(record)

    def records(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._records)

    def reset(self) -> None:
        with self._lock:
            self._records = []


_collector = _Collector()


def enable() -> None:
    """开启采集（runner 调用，会清空历史记录）"""
    _collector.enable()


def disable() -> None:
    _collector.disable()


def is_enabled() -> bool:
    return _collector.enabled


def records() -> list[dict[str, Any]]:
    return _collector.records()


def reset() -> None:
    _collector.reset()


def record(node: str, latency_ms: float | None = None, **extra: Any) -> None:
    """记录一条基准数据（无 token，例如搜索、重试计数）。"""
    if not _collector.enabled:
        return
    entry: dict[str, Any] = {"node": node, **extra}
    if latency_ms is not None:
        entry["latency_ms"] = round(latency_ms, 3)
    _collector.add(entry)


def extract_usage(response: Any) -> dict[str, int] | None:
    """从 langchain AIMessage 提取 token 用量，兼容多种字段位置。

    - langchain 0.3+: AIMessage.usage_metadata = {input_tokens, output_tokens, total_tokens, ...}
    - DeepSeek prompt cache 字段可能挂在 input_token_details 下
    - 旧版兼容: response_metadata["token_usage"]
    """
    if response is None:
        return None

    um = getattr(response, "usage_metadata", None)
    if isinstance(um, dict) and um:
        out: dict[str, int] = {}
        for k in ("input_tokens", "output_tokens", "total_tokens"):
            if isinstance(um.get(k), int):
                out[k] = um[k]
        details = um.get("input_token_details") or {}
        if isinstance(details, dict):
            for k in ("cache_read", "cache_creation"):
                if isinstance(details.get(k), int):
                    out[f"prompt_cache_{k}"] = details[k]
        if out:
            return out

    rm = getattr(response, "response_metadata", None)
    if isinstance(rm, dict):
        tu = rm.get("token_usage")
        if isinstance(tu, dict) and tu:
            out = {}
            for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if isinstance(tu.get(k), int):
                    out[k] = tu[k]
            if out:
                return out

    return None


async def timed(node: str, awaitable: Awaitable[Any], **extra: Any) -> Any:
    """对 awaitable 计时并记录（结果若含 token 用量则一并记录），返回其结果。"""
    start = time.perf_counter()
    result = await awaitable
    latency_ms = (time.perf_counter() - start) * 1000.0
    entry: dict[str, Any] = {"node": node, "latency_ms": round(latency_ms, 3), **extra}
    tokens = extract_usage(result)
    if tokens:
        entry["tokens"] = tokens
    _collector.add(entry)
    return result
