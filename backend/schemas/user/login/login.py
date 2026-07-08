from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    user_id: int
    email: str
    username: str
    photo: str
