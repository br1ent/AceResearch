"""对话管理服务"""
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.chat import Conversation, Message


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, title: str = "新对话", mode: str = "research") -> Conversation:
        conv = Conversation(user_id=user_id, title=title, mode=mode)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def update_title(self, conv_id: int, title: str) -> Conversation | None:
        conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            conv.title = title
            self.db.commit()
            self.db.refresh(conv)
        return conv

    def list_by_user(self, user_id: int) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.update_at))
            .all()
        )

    def get_by_id(self, conv_id: int, user_id: int) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conv_id, Conversation.user_id == user_id)
            .first()
        )

    def get_messages(self, conv_id: int, user_id: int = 0, limit: int = 30, offset: int = 0) -> list[Message]:
        q = self.db.query(Message).filter(Message.conversation_id == conv_id)
        if user_id:
            q = q.filter(Message.user_id == user_id)
        return q.order_by(Message.create_at.desc()).offset(offset).limit(limit).all()[::-1]

    def add_message(
        self,
        conv_id: int,
        role: str,
        content: str,
        msg_type: str = "text",
        metadata_json: str | None = None,
    ) -> Message:
        conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        uid = conv.user_id if conv else 0
        msg = Message(
            conversation_id=conv_id, user_id=uid, role=role, content=content,
            msg_type=msg_type, metadata_json=metadata_json,
        )
        self.db.add(msg)
        if conv:
            conv.update_at = datetime.datetime.now()
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def delete(self, conv_id: int, user_id: int) -> bool:
        """删除对话（验证归属）"""
        conv = self.db.query(Conversation).filter(
            Conversation.id == conv_id, Conversation.user_id == user_id
        ).first()
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True
