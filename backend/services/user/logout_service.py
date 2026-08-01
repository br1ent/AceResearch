from utils.auth import revoke_user_tokens


class LogoutService:
    def logout(self, user_id: int | None = None) -> dict:
        if user_id:
            revoke_user_tokens(user_id)
        return {"success": True, "message": "已退出登录"}
