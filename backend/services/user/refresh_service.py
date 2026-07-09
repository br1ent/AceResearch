from utils.auth import decode_token, create_access_token


class RefreshService:
    def refresh(self, refresh_token: str, access_token: str | None) -> dict:
        # 1. 检查有没有 refresh token
        if not refresh_token:
            return {
                "success": False,
                "message": "未登录，请先登录",
                "status_code": 401,
            }

        # 2. access token 还有效，不刷新直接返回
        if access_token and decode_token(access_token) is not None:
            return {
                "success": True,
                "data": {"access_token": access_token},
            }

        # 3. access token 过期或不存在，用 refresh token 签发新的
        payload = decode_token(refresh_token)
        if payload is None:
            return {
                "success": False,
                "message": "登录已过期，请重新登录",
                "status_code": 401,
            }

        new_access_token = create_access_token({"sub": payload.get("sub")})
        return {
            "success": True,
            "data": {"access_token": new_access_token},
        }
