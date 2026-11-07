from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.logger import logger


_FIELD_NAMES = {
    "email": "邮箱",
    "password": "密码",
    "confirm_password": "确认密码",
    "username": "用户名",
    "code": "验证码",
}


def _translate_error(err: dict) -> str:
    """把 Pydantic 校验错误翻译成中文提示"""
    loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
    field = _FIELD_NAMES.get(loc, loc) if loc else "参数"
    err_type = err.get("type", "")
    ctx = err.get("ctx") or {}

    if err_type == "missing":
        return f"{field}不能为空"
    if err_type == "string_too_short":
        return f"{field}长度不能少于 {ctx.get('min_length', '')} 个字符"
    if err_type == "string_too_long":
        return f"{field}长度不能超过 {ctx.get('max_length', '')} 个字符"
    if err_type in ("value_error", "assert_error"):
        if loc == "email":
            return "邮箱格式不正确"
        return f"{field}不合法"
    if "email" in err_type:
        return "邮箱格式不正确"
    if err_type.endswith("_type") or err_type.endswith("_parsing"):
        return f"{field}格式不正确"
    return f"{field}不合法"


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一错误响应结构 {"success": false, "message": ...}"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "请求失败"
        if detail == "Not Found":
            detail = "请求的资源不存在"
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        message = _translate_error(first) if first else "请求参数不合法"
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": message},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"未捕获异常 {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "服务器内部错误，请稍后重试"},
        )
