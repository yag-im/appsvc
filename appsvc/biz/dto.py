import typing as t
from enum import (
    Enum,
    StrEnum,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
)

from appsvc.biz.hw import GpuModel
from appsvc.services.dto.jukeboxsvc import (
    DcRegion,
    WindowSystem,
)


def _enum_by_name[E: Enum](enum: type[E]) -> t.Callable[[t.Any], t.Any]:
    def parse(v: t.Any) -> t.Any:
        if isinstance(v, str) and not isinstance(v, enum):
            try:
                return enum[v]
            except KeyError:
                raise ValueError(f"Must be one of: {', '.join(enum.__members__)}.") from None
        return v

    return parse


def _enum_name(v: Enum | None) -> str | None:
    return v.name if v is not None else None


# these enums are (de)serialized by member name rather than value (API/DB compatibility)
GpuModelByName = t.Annotated[GpuModel, BeforeValidator(_enum_by_name(GpuModel)), PlainSerializer(_enum_name)]


class RequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppsLib(BaseModel):
    favorite_games: list[int] = Field(default_factory=list)
    recently_played_games: list[int] = Field(default_factory=list)


class ContainerOpDescr(RequestDTO):
    id: str
    node_id: str


class ContainerDescr(ContainerOpDescr):
    region: DcRegion
    cpuset_cpus: list[int]


class WsConnDC(RequestDTO):
    id: str
    consumer_id: str


class AppReleaseDetails(BaseModel):
    class Company(BaseModel):
        id: int
        name: str | None = None
        developer: bool | None = None
        porting: bool | None = None
        publisher: bool | None = None
        supporting: bool | None = None

    class MediaAssets(BaseModel):
        class Cover(BaseModel):
            image_id: str

        class Screenshot(BaseModel):
            width: int
            height: int
            image_id: str

        cover: Cover | None = None
        screenshots: list[Screenshot] | None = None

    class Runner(BaseModel):
        name: str
        ver: str | None = None
        window_system: WindowSystem | None = None

    class AppReqs(BaseModel):
        class HwReqs(BaseModel):
            gpu: GpuModelByName | None = None
            memory: int = 0
            memory_shared: int = 0
            nanocpus: int = 0

        class UaReqs(BaseModel):
            lock_pointer: bool = False

        color_bits: int | None = None
        screen_width: int
        screen_height: int
        hw: HwReqs = Field(default_factory=HwReqs)
        midi: bool = False
        ua: UaReqs = Field(default_factory=UaReqs)
        loading_duration: int | None = 0

    class GameRefs(BaseModel):
        ag_id: str | int | None = None
        lutris_id: str | None = None
        mg_id: int | None = None
        pcgw_id: str | None = None
        qz_id: int | None = None

    class IgdbDescr(BaseModel):
        id: int
        slug: str
        similar_ids: list[int] | None = None

    class AppPlatform(BaseModel):
        id: int
        name: str | None = None
        abbreviation: str | None = None
        alternative_name: str | None = None
        slug: str | None = None

    class Distro(BaseModel):
        files: list[str]
        format: str
        url: str

    addl_artifacts: dict[str, t.Any] | None = None
    alternative_names: list[str] | None = None
    app_reqs: AppReqs
    companies: list[Company]
    distro: Distro
    esrb_rating: int | None = None
    igdb: IgdbDescr
    id: int
    is_visible: bool | None = None
    lang: str | None = None
    long_descr: str | None = None
    media_assets: MediaAssets
    media_assets_localized: MediaAssets | None = None
    name: str | None = None
    platform: AppPlatform
    refs: GameRefs
    runner: Runner
    short_descr: str | None = None
    uuid: str
    uuidv4: str | None = None
    year_released: int | None = None
    tags: list[str] | None = None


class RunAppRequestDTO(RequestDTO):
    app_release_uuid: str
    user_id: int
    ws_conn: WsConnDC
    preferred_dcs: list[str] | None = Field(default_factory=list)


class RunAppResponseDTO(BaseModel):
    container: ContainerDescr


class PauseAppRequestDTO(RequestDTO):
    container: ContainerOpDescr


class ResumeAppRequestDTO(RequestDTO):
    container: ContainerOpDescr
    ws_conn: WsConnDC


class StopAppRequestDTO(RequestDTO):
    container: ContainerOpDescr


class SearchAppsOrderBy(StrEnum):
    TS_ADDED = "ts_added"
    YEAR_RELEASED = "year_released"
    NAME = "name"


class AgeMode(StrEnum):
    KID = "K"
    TEEN = "T"
    ADULT = "A"


class MyStuffType(StrEnum):
    FAVORITES = "favorites"
    RECENTLY_PLAYED = "recently_played"


MyStuffTypeByName = t.Annotated[MyStuffType, BeforeValidator(_enum_by_name(MyStuffType)), PlainSerializer(_enum_name)]

DEFAULT_AGE_MODE = AgeMode.TEEN


class SearchAppsRequestDTO(RequestDTO):
    app_name: t.Annotated[str | None, Field(min_length=2)] = None
    publisher_name: str | None = None
    lang: str | None = None
    my_stuff: MyStuffTypeByName | None = None
    user_id: int | None = None
    offset: int = 0
    limit: int = 100
    order_by: SearchAppsOrderBy | None = SearchAppsOrderBy.TS_ADDED


class SearchAppsResponseItem(BaseModel):
    cover_image_id: str | None = None
    esrb_rating: int | None = None
    id: str
    lang: str | None = None
    name: str | None = None
    slug: str | None = None
    year_released: int | None = None
    platform: str | None = None
    distro_format: str | None = None
    tags: list[str] | None = None


class SearchAppsResponseDTO(BaseModel):
    apps: list[SearchAppsResponseItem] = Field(default_factory=list)


class SearchAppsAclRequestDTO(RequestDTO):
    app_name: t.Annotated[str | None, Field(min_length=2)] = None
    publisher_name: t.Annotated[str | None, Field(min_length=2)] = None
    my_stuff: MyStuffTypeByName | None = None
    user_id: int | None = None


class SearchAppsAclResponseDTO(BaseModel):
    acl: list[str]
