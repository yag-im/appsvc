import datetime
import typing as t

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    DATE,
    JSONB,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from appsvc.biz import sqldb


class AppDAO(sqldb.Model):
    __tablename__ = "games"
    __table_args__ = {"schema": "games"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    addl_artifacts: Mapped[dict[str, t.Any] | None] = mapped_column(JSONB)
    alternative_names: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    companies: Mapped[list[dict[str, t.Any]]] = mapped_column(JSONB)
    esrb_rating: Mapped[int | None] = mapped_column(Integer)
    genres: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    igdb: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    long_descr: Mapped[str | None] = mapped_column(String)
    media_assets: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    name: Mapped[str] = mapped_column(String)
    platforms: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    refs: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    short_descr: Mapped[str | None] = mapped_column(String)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))


class AppCompanyDAO(sqldb.Model):
    __tablename__ = "companies"
    __table_args__ = {"schema": "games"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)


class AppPlatformDAO(sqldb.Model):
    __tablename__ = "platforms"
    __table_args__ = {"schema": "games"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    abbreviation: Mapped[str | None] = mapped_column(String)
    alternative_name: Mapped[str | None] = mapped_column(String)
    slug: Mapped[str | None] = mapped_column(String)


class AppReleaseDAO(sqldb.Model):
    __tablename__ = "releases"
    __table_args__ = {"schema": "games"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    app_reqs: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    game: Mapped[AppDAO] = relationship(AppDAO)
    game_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(AppDAO.id))
    companies: Mapped[list[dict[str, t.Any]]] = mapped_column(JSONB)
    distro: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    is_visible: Mapped[bool | None] = mapped_column(Boolean)
    lang: Mapped[str | None] = mapped_column(String)
    media_assets: Mapped[dict[str, t.Any] | None] = mapped_column(JSONB)
    name: Mapped[str | None] = mapped_column(String)
    platform: Mapped[AppPlatformDAO] = relationship(AppPlatformDAO)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey(AppPlatformDAO.id))
    runner: Mapped[dict[str, t.Any]] = mapped_column(JSONB)
    uuid: Mapped[str] = mapped_column(String)
    # legacy uuid; keeping it because it's a part of app path in appstor for older releases
    uuidv4: Mapped[str | None] = mapped_column(String)
    year_released: Mapped[int | None] = mapped_column(Integer)


class UsersDcsDAO(sqldb.Model):
    __tablename__ = "users_dcs"
    __table_args__ = {"schema": "stats"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dcs: Mapped[dict[str, list[float]]] = mapped_column(JSONB)
    user_id: Mapped[int] = mapped_column(BigInteger)


class UserDAO(sqldb.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "accounts"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(256), unique=False)
    name: Mapped[str | None] = mapped_column(String(256), unique=False)
    tz: Mapped[str] = mapped_column(String, nullable=False, server_default="UTC")
    apps_lib: Mapped[dict[str, t.Any] | None] = mapped_column(JSONB)
    dob: Mapped[datetime.date] = mapped_column(DATE, nullable=False, server_default="1970-01-01")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="TRUE")
