"""Chat 相关 Pydantic Schema"""
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: str = Field(default="新对话", max_length=100)
    mode: str = Field(default="research", pattern=r"^(chat|research)$")


class ConversationOut(BaseModel):
    """对话响应"""
    id: int
    title: str
    mode: str
    created_at: datetime = Field(validation_alias="create_at")
    updated_at: datetime = Field(validation_alias="update_at")

    model_config = {"from_attributes": True}


class ConversationListOut(BaseModel):
    """对话列表响应"""
    success: bool
    data: list[ConversationOut]


class MessageOut(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    msg_type: str
    created_at: datetime = Field(validation_alias="create_at")

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    """发送消息请求（通用：闲聊/研究）"""
    conversation_id: int | None = Field(default=None, description="已有对话ID，为空则新建")
    message: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="chat", pattern=r"^(chat|research)$")
