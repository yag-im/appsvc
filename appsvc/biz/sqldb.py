import typing as t
from contextvars import ContextVar

from fastapi import (
    FastAPI,
    Request,
    Response,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    scoped_session,
    sessionmaker,
)
from starlette.concurrency import run_in_threadpool

_request_scope: ContextVar[object | None] = ContextVar("sqldb_request_scope", default=None)

# scoped per request, not per thread: a request's sync code may hop between threadpool threads
session = scoped_session(sessionmaker(), scopefunc=_request_scope.get)


class Model(DeclarativeBase):
    query = session.query_property()


def init_app(app: FastAPI, url: str, engine_options: dict[str, t.Any]) -> None:
    session.configure(bind=create_engine(url, **engine_options))

    @app.middleware("http")
    async def scope_session_to_request(
        request: Request, call_next: t.Callable[[Request], t.Awaitable[Response]]
    ) -> Response:
        token = _request_scope.set(object())
        try:
            return await call_next(request)
        finally:
            await run_in_threadpool(session.remove)
            _request_scope.reset(token)
