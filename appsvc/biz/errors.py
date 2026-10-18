import json
import logging
import typing as t

from fastapi import (
    FastAPI,
    Request,
    Response,
)
from fastapi.exceptions import RequestValidationError

ERROR_APP_OP = (1409, "app operational error")
ERROR_APP_RELEASE_NOT_FOUND = (1404, "app release not found")
ERROR_JUKEBOXSVC_CONTAINER_NOT_FOUND = (1404, "jukeboxsvc: container not found")
ERROR_JUKEBOXSVC = (1409, "jukeboxsvc exception")
ERROR_UNKNOWN = (1500, "unknown error")

log = logging.getLogger("appsvc")


class BizException(Exception):
    def __init__(self, code: t.Optional[int] = None, message: t.Optional[t.Any] = None) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class AppOpException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_APP_OP[0]
        message = message or ERROR_APP_OP[1]
        super().__init__(code, message)


class AppReleaseNotFoundException(BizException):
    def __init__(self) -> None:
        code = ERROR_APP_RELEASE_NOT_FOUND[0]
        message = ERROR_APP_RELEASE_NOT_FOUND[1]
        super().__init__(code, message)


class JukeboxSvcException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_JUKEBOXSVC[0]
        message = message or ERROR_JUKEBOXSVC[1]
        super().__init__(code, message)


class ContainerNotFoundException(BizException):
    def __init__(self, message: t.Optional[t.Any] = None) -> None:
        code = ERROR_JUKEBOXSVC_CONTAINER_NOT_FOUND[0]
        message = message or ERROR_JUKEBOXSVC_CONTAINER_NOT_FOUND[1]
        super().__init__(code, message)


def _error_messages(e: RequestValidationError) -> dict[str, t.Any]:
    """Groups errors into a nested {field: {subfield: [messages]}} dict."""
    res: dict[str, t.Any] = {}
    for err in e.errors():
        # loc[0] is "body", "query", etc.; json_invalid loc holds a char offset, not a field
        loc = err["loc"][1:] if err["type"] != "json_invalid" else ()
        path = [str(p) for p in loc] or ["_schema"]
        node = res
        for p in path[:-1]:
            node = node.setdefault(p, {})
        node.setdefault(path[-1], []).append(err["msg"])
    return res


def init_app(app: FastAPI) -> None:
    """Inits error handlers."""

    # HTTPException (404, 405, etc.) is handled by FastAPI's default handler
    @app.exception_handler(Exception)
    async def handle_exception(_: Request, e: Exception) -> Response:
        res = json.dumps({"code": ERROR_UNKNOWN[0], "message": ERROR_UNKNOWN[1]})
        log.exception(e, exc_info=e)
        return Response(res, media_type="application/json", status_code=500)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, e: RequestValidationError) -> Response:
        res = json.dumps(
            {
                "code": 1400,
                "message": _error_messages(e),
            }
        )
        log.error(res)
        return Response(res, media_type="application/json", status_code=400)

    @app.exception_handler(BizException)
    async def handle_biz_exception(_: Request, e: BizException) -> Response:
        res = json.dumps(
            {
                "code": e.code,
                "message": e.message,
            }
        )
        log.error(res)
        return Response(res, media_type="application/json", status_code=409)
