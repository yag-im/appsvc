# sync with jukeboxsvc (jukeboxsvc/dto/container.py)

from enum import StrEnum

from pydantic import BaseModel

from appsvc.biz.hw import GpuModel


class DcRegion(StrEnum):
    EU_CENTRAL_1 = "eu-central-1"
    US_EAST_1 = "us-east-1"
    US_WEST_1 = "us-west-1"


class WindowSystem(StrEnum):
    X11 = "x11"
    WAYLAND = "wayland"


class AppPlatform(StrEnum):
    DOS = "dos"
    MAC = "mac"
    PHILIPS_CD_I = "philips-cd-i"
    SEGA_GENESIS = "genesis-slash-megadrive"
    WINDOWS = "win"
    ZX_SPECTRUM = "zxs"
    AMIGA = "amiga"
    TRS_80 = "trs-80"


class WsConnDC(BaseModel):
    """Websocket connection (sigsvc) parameters."""

    consumer_id: str  # peer_id of the party awaiting for a stream
    id: str  # unique ws connection id (used as a sticky session cookie value)


class RunContainerRequestDTO(BaseModel):
    class AppDescr(BaseModel):
        # slug and release_uuid are also parts of an app path in appstor
        slug: str  # igdb slug, e.g. the-pink-panther-hokus-pokus-pink
        release_uuid: str  # unique release id, e.g.: 019c887a-f4e2-7dcc-a793-678c0e0b9f6e
        release_uuidv4: str | None = None  # legacy release uuid; part of app path in appstor for older releases
        platform: AppPlatform

    class Requirements(BaseModel):
        class AppRequirements(BaseModel):
            color_bits: int
            midi: bool
            screen_height: int
            screen_width: int
            loading_duration: int | None = 0

        class ContainerSpecs(BaseModel):
            class Runner(BaseModel):
                name: str
                ver: str
                window_system: WindowSystem

            runner: Runner

        class HardwareRequirements(BaseModel):
            # could be for either app itself (3D game) or streamd
            # (powerfull codec / highres may require a dedicated GPU)
            gpu: GpuModel | None = None
            memory: int  # memory required by apps running inside a container (game, runner and streamd)
            memory_shared: int | None = None  # shared memory required by apps (in bytes)
            nanocpus: int  # nanocpus required by apps running inside a container (game, runner and streamd)

        app: AppRequirements
        container: ContainerSpecs
        hw: HardwareRequirements

    app_descr: AppDescr
    # TODO: use DcRegion enum for "preferred_dcs"
    preferred_dcs: list[str]
    reqs: Requirements
    user_id: int
    ws_conn: WsConnDC


class RunContainerResponseDTO(BaseModel):
    class NodeDescr(BaseModel):
        id: str
        api_uri: str
        region: DcRegion

    class ContainerDescr(BaseModel):
        id: str
        cpuset_cpus: list[int]

    node: NodeDescr
    container: ContainerDescr


class ResumeContainerRequestDTO(BaseModel):
    ws_conn: WsConnDC
