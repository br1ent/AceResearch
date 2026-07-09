import re

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserLogin(BaseModel):
    email: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6)

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("邮箱格式不正确")
        return v
