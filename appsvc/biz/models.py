from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB,
)
from sqlalchemy.orm import relationship

from appsvc.biz.sqldb import sqldb


class AppDAO(sqldb.Model):
    __tablename__ = "games"
    __table_args__ = {"schema": "games"}
    id = Column(BigInteger, primary_key=True)
    addl_artifacts = Column(JSONB)
    alternative_names = Column(ARRAY(String))
    companies = Column(JSONB)
    esrb_rating = Column(Integer)
    genres = Column(ARRAY(Integer))
    igdb = Column(JSONB)
    long_descr = Column(String)
    media_assets = Column(JSONB)
    name = Column(String)
    platforms = Column(ARRAY(Integer))
    refs = Column(JSONB)
    short_descr = Column(String)
    tags = Column(ARRAY(String))


class AppCompanyDAO(sqldb.Model):
    __tablename__ = "companies"
    __table_args__ = {"schema": "games"}
    id = Column(Integer, primary_key=True)
    name = Column(String)


class AppPlatformDAO(sqldb.Model):
    __tablename__ = "platforms"
    __table_args__ = {"schema": "games"}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbreviation = Column(String)
    alternative_name = Column(String)
    slug = Column(String)


class AppReleaseDAO(sqldb.Model):
    __tablename__ = "releases"
    __table_args__ = {"schema": "games"}
    id = Column(BigInteger, primary_key=True)
    app_reqs = Column(JSONB)
    game = relationship(AppDAO)
    game_id = Column(BigInteger, ForeignKey(AppDAO.id))
    companies = Column(JSONB)
    distro = Column(JSONB)
    is_visible = Column(Boolean)
    lang = Column(String)
    media_assets = Column(JSONB)
    name = Column(String)
    platform = relationship(AppPlatformDAO)
    platform_id = Column(Integer, ForeignKey(AppPlatformDAO.id))
    runner = Column(JSONB)
    ts_added = Column(TIMESTAMP)
    uuid = Column(String)
    year_released = Column(Integer)


class UsersDcsDAO(sqldb.Model):
    __tablename__ = "users_dcs"
    __table_args__ = {"schema": "stats"}
    id = Column(BigInteger, primary_key=True)
    dcs = Column(JSONB)
    user_id = Column(BigInteger)
