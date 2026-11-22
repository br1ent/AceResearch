"""统一日志：loguru + 结构化 JSON + 关联 ID 默认值。

文件日志按 {node}_{status}_{date}.log 命名，每日 0 点自然滚动、保留 7 天：
- node：Agent 节点名（planner/researcher/analyst/writer/reviewer/summarizer），非节点日志归入 app
- status：error（WARNING 及以上）或 info（INFO/DEBUG）
- date：年-月-日

用法：
    1. 任务入口用 logger.contextualize(conversation_id=..., report_id=..., user_id=...) 绑定关联 ID，
       该上下文随 asyncio await 自动传播到所有子调用（contextvars）。
    2. 任意模块 `from utils.logger import logger` 后直接 logger.info/warning/error/exception。
    3. 结构化字段（node / latency_ms / tokens）通过 logger.info(..., node=..., latency_ms=...) 传入 extra。
"""
import datetime
import sys
import threading
import time
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).parent.parent / "log"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

# 默认 extra：未绑定关联 ID 时用 "-" 兜底，避免格式化 KeyError
logger.configure(extra={"conversation_id": "-", "report_id": "-", "user_id": "-", "node": "-"})

_CONSOLE_FMT = (
    "{time:HH:mm:ss.SSS} | {level: <8} | "
    "conv={extra[conversation_id]} report={extra[report_id]} | "
    "{extra[node]} | {message}"
)
_FILE_FMT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "conv={extra[conversation_id]} report={extra[report_id]} | "
    "{extra[node]} | {message}"
)

# 1) 控制台（开发看）
logger.add(sys.stderr, level="INFO", format=_CONSOLE_FMT)

# 7 天日志清理（每小时节流一次）
_cleanup_lock = threading.Lock()
_last_cleanup = 0.0


def _cleanup_old_logs() -> None:
    """删除 7 天前的 *.log 文件（每小时最多执行一次）。"""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < 3600:
        return
    with _cleanup_lock:
        if now - _last_cleanup < 3600:
            return
        _last_cleanup = now
        cutoff = now - 7 * 86400
        for p in LOG_DIR.glob("*.log"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
            except OSError:
                pass


def _daily_file_sink(message) -> None:
    """按 {node}_{status}_{date}.log 写文件，status 只分 error / info。"""
    record = message.record
    node = record["extra"].get("node") or "-"
    if node == "-":
        node = "app"
    status = "error" if record["level"].no >= 30 else "info"
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filepath = LOG_DIR / f"{node}_{status}_{date_str}.log"
    with filepath.open("a", encoding="utf-8") as f:
        f.write(str(message) + "\n")
    _cleanup_old_logs()


# 2) 文件（人看，全量 DEBUG，每日滚动 + 7 天保留）
logger.add(_daily_file_sink, level="DEBUG", format=_FILE_FMT)

# 3) JSON（机器看，每日滚动 + 7 天保留）
logger.add(
    LOG_DIR / "app.jsonl",
    rotation="00:00",
    retention="7 days",
    level="INFO",
    serialize=True,
    encoding="utf-8",
)

# 兼容旧引用（reviewer.py 仍在用）
review_logger = logger.bind(name="reviewer", node="reviewer")
