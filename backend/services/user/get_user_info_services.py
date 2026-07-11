from models.user import User
from schemas.user.get_user_info import GetUserInfoOut


class GetUserInfoServices:
    def get_user_info(self, user: User) -> dict:
        user_out = GetUserInfoOut.model_validate(user)
        return {"success": True, "data": user_out.model_dump()}
