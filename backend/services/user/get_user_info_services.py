from models.user import User
from schemas.user.get_user_info import GetUserInfoOut
from config.settings import get_settings

settings = get_settings()


class GetUserInfoServices:
    def get_user_info(self, user: User) -> dict:
        user_out = GetUserInfoOut.model_validate(user)
        data = user_out.model_dump()
        photo = data.get("photo") or ""
        if photo.startswith("/"):
            data["photo"] = f"{settings.BASE_URL}{photo}"
        return {"success": True, "data": data}
