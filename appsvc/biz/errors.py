import json
import logging
import typing as t

from flask import (
    Flask,
    Response,
)
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

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


def init_app(app: Flask) -> None:
    """Inits error handlers.

    Make sure FLASK_PROPAGATE_EXCEPTIONS is set to `true`, otherwise errorhandlers will be unreachable.
    """

    @app.errorhandler(Exception)
    def handle_exception(e: Exception) -> Response:
        if isinstance(e, HTTPException):
            return e
        res = json.dumps({"code": ERROR_UNKNOWN[0], "message": ERROR_UNKNOWN[1]})
        log.exception(e)
        return Response(res, mimetype="application/json", status=500)

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError) -> Response:
        res = json.dumps(
            {
                "code": 1400,
                "message": e.messages,
            }
        )
        log.error(res)
        return Response(res, mimetype="application/json", status=400)

    @app.errorhandler(BizException)
    def handle_biz_exception(e: BizException) -> Response:
        res = json.dumps(
            {
                "code": e.code,
                "message": e.message,
            }
        )
        log.error(res)
        return Response(res, mimetype="application/json", status=409)
