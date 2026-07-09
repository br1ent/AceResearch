from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)