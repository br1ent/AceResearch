from pydantic import BaseModel


class GetUserInfoOut(BaseModel):
    id: int
    username: str
    email: str
    photo: str

    model_config = {"from_attributes": True}