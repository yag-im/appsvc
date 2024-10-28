import logging

from flask import Flask


def init_app(app: Flask) -> None:
    # log setup
    # TODO: use app.config["DEBUG"] flag for log_level
    log_level = logging.DEBUG

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    app_log = logging.getLogger("appsvc")
    app_log.handlers.clear()
    app_log.addHandler(handler)
    app_log.setLevel(log_level)
    app_log.propagate = False

    root_log = logging.getLogger()
    root_log.handlers.clear()
    root_log.addHandler(handler)
    root_log.setLevel(log_level)
    root_log.propagate = False

    # talkative modules:
    logging.getLogger("urllib3").setLevel(logging.INFO)
    # change to INFO to track all queries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)
