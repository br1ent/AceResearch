"""对话管理服务"""
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.chat import Conversation, Message
from services.chat.research import ResearchService


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

    def get_messages(self, conv_id: int, limit: int = 100) -> list[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conv_id)
            .order_by(Message.create_at)
            .limit(limit)
            .all()
        )

    def add_message(
        self,
        conv_id: int,
        role: str,
        content: str,
        msg_type: str = "text",
        metadata_json: str | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conv_id,
            role=role,
            content=content,
            msg_type=msg_type,
            metadata_json=metadata_json,
        )
        self.db.add(msg)

        # 更新对话时间
        conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            import datetime
            conv.update_at = datetime.datetime.now()

        self.db.commit()
        self.db.refresh(msg)
        return msg
