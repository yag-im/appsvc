from fastapi import APIRouter

from appsvc.biz import app as biz
from appsvc.biz.dto import (
    AppReleaseDetails,
    PauseAppRequestDTO,
    ResumeAppRequestDTO,
    RunAppRequestDTO,
    RunAppResponseDTO,
    SearchAppsAclRequestDTO,
    SearchAppsAclResponseDTO,
    SearchAppsRequestDTO,
    SearchAppsResponseDTO,
    StopAppRequestDTO,
)

router = APIRouter(prefix="/apps")


@router.get("/{app_release_uuid}")
def get_app_release(app_release_uuid: str) -> AppReleaseDetails:
    """Gets app release details."""
    return biz.get_app_release(app_release_uuid)


@router.post("/run")
def run_app(req: RunAppRequestDTO) -> RunAppResponseDTO:
    """Runs a new app."""
    return biz.run_app(req)


@router.post("/pause")
def pause_app(req: PauseAppRequestDTO) -> str:
    """Pauses a running app."""
    biz.pause_app(req)
    return ""


@router.post("/resume")
def resume_app(req: ResumeAppRequestDTO) -> str:
    """Resumes a paused app.

    May require a context switch (sigsvc server change) so it accepts a new set of ws_conn parameters.
    """
    biz.resume_app(req)
    return ""


@router.post("/stop")
def stop_app(req: StopAppRequestDTO) -> str:
    """Stops a running app."""
    biz.stop_app(req)
    return ""


@router.post("/search/acl")
def search_apps_acl(req: SearchAppsAclRequestDTO) -> SearchAppsAclResponseDTO:
    """Search apps helper: auto-complete lists."""
    return SearchAppsAclResponseDTO(acl=biz.search_apps_acl(req))


@router.post("/search")
def search_apps(req: SearchAppsRequestDTO) -> SearchAppsResponseDTO:
    """Search apps."""
    return SearchAppsResponseDTO(apps=biz.search_apps(req))
