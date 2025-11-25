import json
import logging
import os
from statistics import median

from sqlalchemy import (
    func,
    text,
)
from sqlalchemy.orm import contains_eager

from appsvc.biz.dto import (
    AppReleaseDetails,
    ContainerDescr,
    ContainerOpDescr,
    PauseAppRequestDTO,
    ResumeAppRequestDTO,
    RunAppRequestDTO,
    RunAppResponseDTO,
    SearchAppsAclRequestDTO,
    SearchAppsOrderBy,
    SearchAppsRequestDTO,
    SearchAppsResponseItem,
    StopAppRequestDTO,
)
from appsvc.biz.errors import (
    AppOpException,
    AppReleaseNotFoundException,
    ContainerNotFoundException,
    JukeboxSvcException,
)
from appsvc.biz.misc import log_input_output
from appsvc.biz.models import (
    AppCompanyDAO,
    AppDAO,
    AppReleaseDAO,
    UsersDcsDAO,
)
from appsvc.biz.sqldb import sqldb
from appsvc.services import jukeboxsvc
from appsvc.services.dto.jukeboxsvc import (
    AppPlatform,
    RunContainerRequestDTO,
    RunContainerResponseDTO,
    VideoEnc,
    WindowSystem,
    WsConnDC,
)

APPS_SEARCH_LIMIT = 200
APPS_ACL_SEARCH_LIMIT = 25

DEFAULT_APP_REQ_MIDI = False
DEFAULT_APP_REQ_COLOR_BITS = 24
MIN_COLOR_BITS = 16  # xorg fails to start with lower Depth
MAX_COLOR_BITS = 24  # xorg fails to start with higher Depth
MIN_SCREEN_HEIGHT = 400  # xorg fails to start with lower
MIN_SCREEN_WIDTH = 640  # xorg fails to start with lower
DEFAULT_HW_REQ_DGPU = False
DEFAULT_HW_REQ_IGPU = False
DEFAULT_HW_REQ_MEMORY = 1 * 1024 * 1024 * 1024  # 1GB
DEFAULT_HW_REQ_MEMORY_SHARED = None
DEFAULT_HW_REQ_NANOCPUS = 1 * 1_000_000_000  # 1 CPU core

DATA_CENTERS: list[str] = json.loads(os.environ["DATA_CENTERS"])
RUNNERS_CONF: dict = json.loads(os.environ["RUNNERS_CONF"])
STREAMD_REQS: dict = json.loads(os.environ["STREAMD_REQS"])

ESRB_RATING_T_ID = 10
ESRB_RATING_M_ID = 11
MAX_GOOD_RTT = 0.05  # 50 ms

log = logging.getLogger("appsvc")


def get_app_release(release_uuid: str) -> AppReleaseDetails:
    # support "human-readable" urls (using games.releases.id instead of uuid)
    filter_by_field = AppReleaseDAO.uuid if len(release_uuid) == 36 else AppReleaseDAO.id
    filter_by = [filter_by_field == release_uuid, AppReleaseDAO.is_visible.is_(True)]
    r = AppReleaseDAO.query.filter(*filter_by).first()
    if not r:
        raise AppReleaseNotFoundException
    # fetch company name
    for c in r.companies:
        company_dao = AppCompanyDAO.query.filter_by(id=c["id"]).first()
        c["name"] = company_dao.name
    # norm refs
    for k, v in r.game.refs.items():
        if v in {-1, ""}:
            r.game.refs[k] = None
    return AppReleaseDetails(
        addl_artifacts=r.game.addl_artifacts,
        alternative_names=r.game.alternative_names,
        app_reqs=AppReleaseDetails.AppReqs.Schema().load(r.app_reqs),
        companies=r.companies,
        distro=AppReleaseDetails.Distro.Schema().load(r.distro),
        esrb_rating=r.game.esrb_rating,
        id=r.id,
        igdb=AppReleaseDetails.IgdbDescr.Schema().load(r.game.igdb),
        is_visible=r.is_visible,
        lang=r.lang,
        long_descr=r.game.long_descr,
        media_assets=AppReleaseDetails.MediaAssets.Schema().load(r.game.media_assets),
        media_assets_localized=AppReleaseDetails.MediaAssets.Schema().load(r.media_assets) if r.media_assets else None,
        name=r.name,
        platform=r.platform,
        refs=AppReleaseDetails.GameRefs.Schema().load(r.game.refs),
        runner=AppReleaseDetails.Runner.Schema().load(r.runner),
        short_descr=r.game.short_descr,
        ts_added=r.ts_added,
        uuid=r.uuid,
        year_released=r.year_released,
        tags=r.game.tags,
    )


def get_hw_reqs(
    app_release: AppReleaseDetails, runner_conf: dict
) -> RunContainerRequestDTO.Requirements.HardwareRequirements:
    """Gets hardware requirements.

    Based on app, streamd and runner requirements, e.g. dgpu requirement may come from either app (3D game) or
    streamd (powerfull codec / highres)
    """

    # if not app_release.app_reqs.hw:
    # TODO: this should be a part of
    #    app_release.app_reqs.hw = AppReleaseDetails.AppReqs.HwReqs.Schema().load({})
    hw_req_dgpu = (
        app_release.app_reqs.hw.dgpu or STREAMD_REQS.get("dgpu") or runner_conf.get("dgpu") or DEFAULT_HW_REQ_DGPU
    )
    hw_req_igpu = (
        app_release.app_reqs.hw.igpu or STREAMD_REQS.get("igpu") or runner_conf.get("igpu") or DEFAULT_HW_REQ_IGPU
    )
    hw_req_memory = max(
        app_release.app_reqs.hw.memory,
        STREAMD_REQS.get("memory", 0),
        runner_conf.get("memory", 0),
        DEFAULT_HW_REQ_MEMORY,
    )
    hw_req_memory_shared = (
        app_release.app_reqs.hw.memory_shared
        + STREAMD_REQS.get("memory_shared", 0)
        + runner_conf.get("memory_shared", 0)
    ) or DEFAULT_HW_REQ_MEMORY_SHARED

    hw_req_nanocpus = (
        app_release.app_reqs.hw.nanocpus
        + STREAMD_REQS.get("nanocpus", 0)
        + runner_conf.get("nanocpus", 0)
        + DEFAULT_HW_REQ_NANOCPUS
    )

    return RunContainerRequestDTO.Requirements.HardwareRequirements(
        dgpu=hw_req_dgpu,
        igpu=hw_req_igpu,
        memory=hw_req_memory,
        memory_shared=hw_req_memory_shared,
        nanocpus=hw_req_nanocpus,
    )


def get_streamd_video_enc(streamd_reqs: dict) -> VideoEnc:
    if streamd_reqs.get("igpu"):
        return VideoEnc.GPU_INTEL
    elif streamd_reqs.get("dgpu"):
        return VideoEnc.GPU_NVIDIA
    else:
        return VideoEnc.CPU


@log_input_output
def get_preferred_dcs(user_id: int, known_dcs: list[str]) -> list[str]:
    """Returns DCs sorted in preferred order (fastest first)

    known_dcs: DCs sorted from West to East (geographically)

    When there is a DC with a known max good rtt - return this DC as preferred,
    no need to check other DCs as they would be worse

    # TODO: do not go further to the East if current DC is slower than the previous DC
    """
    user_dcs = sqldb.session.query(UsersDcsDAO).filter(UsersDcsDAO.user_id == user_id).first()
    if not user_dcs:
        # new user
        return known_dcs
    # make default preferred_dcs = {W: .05, E: .051, C: .052}
    preferred_dcs = {k: MAX_GOOD_RTT + (ix / 1000) for ix, k in enumerate(known_dcs)}
    for k, v in user_dcs.dcs.items():
        preferred_dcs[k] = median(v)
    return sorted(preferred_dcs, key=lambda k: preferred_dcs[k])


@log_input_output
def run_app(req: RunAppRequestDTO) -> RunAppResponseDTO:
    app_release: AppReleaseDetails = get_app_release(req.app_release_uuid)
    runner_name = app_release.runner.name
    runner_conf = RUNNERS_CONF[runner_name]

    # preferred_dcs may come directly from the UA (TODO: not supported)
    # or be picked based on the collected webrtc stats
    preferred_dcs: list[str] = req.preferred_dcs or get_preferred_dcs(req.user_id, DATA_CENTERS)
    runner_ver = app_release.runner.ver or runner_conf["ver"]
    runner_window_system = app_release.runner.window_system or WindowSystem(runner_conf["window_system"])

    # turn e.g. 320x200 to 640x400 as xorg wouldn't start
    screen_height = app_release.app_reqs.screen_height
    screen_width = app_release.app_reqs.screen_width
    if screen_height < MIN_SCREEN_HEIGHT or screen_width < MIN_SCREEN_WIDTH:
        screen_height *= 2
        screen_width *= 2

    # same for color-depth: set min/max allowed
    color_bits = min(
        MAX_COLOR_BITS,
        max((app_release.app_reqs.color_bits or DEFAULT_APP_REQ_COLOR_BITS), MIN_COLOR_BITS),
    )

    # wine fix (removes transparent square around the cursor in many games):
    if app_release.runner.name == "wine":
        if color_bits == 16:
            color_bits = 24

    run_container_req: RunContainerRequestDTO = RunContainerRequestDTO(
        app_descr=RunContainerRequestDTO.AppDescr(
            slug=app_release.igdb.slug, release_uuid=app_release.uuid, platform=AppPlatform(app_release.platform.slug)
        ),
        reqs=RunContainerRequestDTO.Requirements(
            app=RunContainerRequestDTO.Requirements.AppRequirements(
                midi=app_release.app_reqs.midi or DEFAULT_APP_REQ_MIDI,
                screen_height=screen_height,
                screen_width=screen_width,
                color_bits=color_bits,
                loading_duration=app_release.app_reqs.loading_duration,
            ),
            container=RunContainerRequestDTO.Requirements.ContainerSpecs(
                runner=RunContainerRequestDTO.Requirements.ContainerSpecs.Runner(
                    name=runner_name, ver=runner_ver, window_system=runner_window_system
                ),
                video_enc=get_streamd_video_enc(streamd_reqs=STREAMD_REQS),
            ),
            hw=get_hw_reqs(app_release, runner_conf),
        ),
        user_id=req.user_id,
        preferred_dcs=preferred_dcs,
        ws_conn=WsConnDC(
            id=req.ws_conn.id,
            consumer_id=req.ws_conn.consumer_id,
        ),
    )
    try:
        run_container_res: RunContainerResponseDTO = jukeboxsvc.run_container(run_container_req)
    except JukeboxSvcException as e:
        raise AppOpException(e.message) from e
    return RunAppResponseDTO(
        container=ContainerDescr(
            id=run_container_res.container.id,
            node_id=run_container_res.node.id,
            region=run_container_res.node.region,
        ),
    )


@log_input_output
def pause_app(req: PauseAppRequestDTO) -> None:
    try:
        jukeboxsvc.pause_container(ContainerOpDescr(id=req.container.id, node_id=req.container.node_id))
    except JukeboxSvcException as e:
        raise AppOpException(e.message) from e


@log_input_output
def resume_app(req: ResumeAppRequestDTO) -> None:
    try:
        jukeboxsvc.resume_container(req)
    except JukeboxSvcException as e:
        raise AppOpException(e.message) from e


@log_input_output
def stop_app(req: StopAppRequestDTO) -> None:
    try:
        jukeboxsvc.stop_container(ContainerOpDescr(id=req.container.id, node_id=req.container.node_id))
    except ContainerNotFoundException:
        log.warning("container %s was already stopped", req.container.id)
    except JukeboxSvcException as e:
        raise AppOpException(e.message) from e


def search_apps_acl(req: SearchAppsAclRequestDTO) -> list[str]:
    q_base = AppReleaseDAO.query
    q_base = q_base.filter(AppReleaseDAO.is_visible.is_(True))
    if req.app_name:
        q_base = q_base.filter(AppReleaseDAO.name.ilike(f"%{req.app_name}%"))
    if req.kids_mode:
        q_base = (
            q_base.join(AppReleaseDAO.game)
            .options(contains_eager(AppReleaseDAO.game))
            .filter((AppDAO.esrb_rating < ESRB_RATING_T_ID) | (AppDAO.esrb_rating.is_(None)))
        )
    res = [ar[0] for ar in q_base.with_entities(AppReleaseDAO.name).limit(APPS_ACL_SEARCH_LIMIT).all()]
    return res


def search_by_publisher(req: SearchAppsRequestDTO, order_sql: str) -> list[AppReleaseDAO]:
    # Use a raw SQL query with LATERAL jsonb_array_elements to reliably unnest the companies JSONB
    # and join to games.companies to filter by publisher name.
    company_mask = f"%{req.publisher_name}%"
    sql_parts = [
        "SELECT r.id",
        "FROM games.releases r",
        "JOIN games.games g ON r.game_id = g.id",
        "JOIN LATERAL jsonb_array_elements(r.companies) elem ON true",
        "JOIN games.companies gc ON (elem->>'id')::int = gc.id",
        "WHERE r.is_visible IS TRUE",
        "AND (elem->>'publisher') = 'true'",
        "AND gc.name ILIKE :company_mask",
    ]
    params: dict[str, str | int] = {"company_mask": company_mask}
    if req.kids_mode:
        sql_parts.append(f"AND ((g.esrb_rating < {ESRB_RATING_T_ID}) OR (g.esrb_rating IS NULL))")

    # ORDER BY using alias 'r' to match releases table alias
    sql_parts.append(f"ORDER BY {order_sql}")
    sql_parts.append("OFFSET :offset LIMIT :limit")
    params["offset"] = req.offset
    params["limit"] = min(APPS_SEARCH_LIMIT, req.limit)
    sql = "\n".join(sql_parts)

    ids_res = sqldb.session.execute(text(sql), params).fetchall()
    ids = [r[0] for r in ids_res]
    if not ids:
        return []

    orm_q = (
        AppReleaseDAO.query.join(AppReleaseDAO.game)
        .options(contains_eager(AppReleaseDAO.game))
        .filter(AppReleaseDAO.id.in_(ids))
    )
    orm_res = orm_q.all()
    orm_map = {r.id: r for r in orm_res}
    return [orm_map[i] for i in ids if i in orm_map]


def search_apps(req: SearchAppsRequestDTO) -> list[SearchAppsResponseItem]:
    q_base = AppReleaseDAO.query.join(AppReleaseDAO.game).options(contains_eager(AppReleaseDAO.game))
    q_base = q_base.filter(AppReleaseDAO.is_visible.is_(True))
    if req.app_name:
        app_name_mask = f"%{req.app_name}%"
        q_base = q_base.filter(
            AppReleaseDAO.name.ilike(app_name_mask)
            | AppDAO.name.ilike(app_name_mask)
            | func.array_to_string(AppDAO.alternative_names, ",").ilike(app_name_mask),
        )
    if req.kids_mode:
        q_base = q_base.filter((AppDAO.esrb_rating < ESRB_RATING_T_ID) | (AppDAO.esrb_rating.is_(None)))
    if req.order_by == SearchAppsOrderBy.TS_ADDED:
        order_by = [AppReleaseDAO.ts_added.desc()]
        order_sql = "r.ts_added DESC"
    elif req.order_by == SearchAppsOrderBy.YEAR_RELEASED:
        order_by = [AppReleaseDAO.year_released.desc(), AppReleaseDAO.ts_added.desc()]
        order_sql = "r.year_released DESC, r.ts_added DESC"
    else:
        order_by = [AppReleaseDAO.name.asc()]
        order_sql = "r.name ASC"
    res: list[AppReleaseDAO]
    if req.publisher_name:
        res = search_by_publisher(req, order_sql)
    else:
        res = q_base.order_by(*order_by).offset(req.offset).limit(min(APPS_SEARCH_LIMIT, req.limit)).all()

    return [
        SearchAppsResponseItem(
            cover_image_id=(
                r.media_assets["cover"]["image_id"] if r.media_assets else r.game.media_assets["cover"]["image_id"]
            ),
            esrb_rating=r.game.esrb_rating,
            id=r.id,
            lang=r.lang,
            name=r.name,
            slug=r.game.igdb["slug"],
            year_released=r.year_released,
            platform=r.platform.slug,
            distro_format=r.distro["format"],
            tags=r.game.tags,
        )
        for r in res
    ]
