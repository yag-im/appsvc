import json
import logging
import os

from fastapi import FastAPI

from appsvc.api import router
from appsvc.biz import (
    errors,
    log,
    sqldb,
)


def create_app() -> FastAPI:
    log.init()

    app = FastAPI()
    app.include_router(router)
    sqldb.init_app(
        app,
        url=f"postgresql+psycopg://{os.environ['SQLDB_USERNAME']}:{os.environ['SQLDB_PASSWORD']}@{os.environ['SQLDB_HOST']}:\
        {os.environ['SQLDB_PORT']}/{os.environ['SQLDB_DBNAME']}",
        engine_options=json.loads(os.environ.get("SQLALCHEMY_ENGINE_OPTIONS", "{}")),
    )
    errors.init_app(app)

    logging.getLogger("appsvc").info("app init completed")

    return app
