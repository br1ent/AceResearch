"""WebSocket 连接管理器"""
from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """管理 WebSocket 连接，支持按 conversation_id 广播"""

    def __init__(self):
        # conversation_id → set of WebSocket
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, conversation_id: int, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(conversation_id, set()).add(ws)

    def disconnect(self, conversation_id: int, ws: WebSocket):
        conns = self._connections.get(conversation_id)
        if conns:
            conns.discard(ws)
            if not conns:
                del self._connections[conversation_id]

    async def broadcast(self, conversation_id: int, data: dict[str, Any]):
        """向对话的所有订阅者推送消息"""
        conns = self._connections.get(conversation_id, set())
        dead = set()
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            conns.discard(ws)
        if not conns and conversation_id in self._connections:
            del self._connections[conversation_id]

    @property
    def active_connections(self) -> dict[int, int]:
        """返回活跃连接数统计"""
        return {cid: len(conns) for cid, conns in self._connections.items()}


# 全局单例
manager = ConnectionManager()
