from pydantic import BaseModel, Field

class UserLogin(BaseModel):
    email: str
    password: str
