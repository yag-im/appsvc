from flask import (
    Response,
    request,
)
from flask_restful import Resource

from appsvc.biz.app import (
    get_app_release,
    pause_app,
    resume_app,
    run_app,
    search_apps,
    search_apps_acl,
    stop_app,
)
from appsvc.biz.dto import (
    GetAppReleaseResponseDTO,
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


class GetAppRelease(Resource):
    def get(self, app_release_uuid: str) -> Response:
        """Gets app release details."""
        res = get_app_release(app_release_uuid)
        return GetAppReleaseResponseDTO.Schema().dump(res), 200


class RunApp(Resource):
    def post(self) -> Response:
        """Runs a new app."""
        req: RunAppRequestDTO = RunAppRequestDTO.Schema().load(data=request.get_json())
        res = run_app(req)
        return RunAppResponseDTO.Schema().dump(res), 200


class PauseApp(Resource):
    def post(self) -> Response:
        """Pauses a running app."""
        req: PauseAppRequestDTO = PauseAppRequestDTO.Schema().load(data=request.get_json())
        pause_app(req)
        return "", 200


class ResumeApp(Resource):
    def post(self) -> Response:
        """Resumes a paused app.

        May require a context switch (sigsvc server change) so it accepts a new set of ws_conn parameters.
        """
        req: ResumeAppRequestDTO = ResumeAppRequestDTO.Schema().load(data=request.get_json())
        resume_app(req)
        return "", 200


class StopApp(Resource):
    def post(self) -> Response:
        """Stops a running app."""
        req: StopAppRequestDTO = StopAppRequestDTO.Schema().load(data=request.get_json())
        stop_app(req)
        return "", 200


class SearchAppsAcl(Resource):
    def post(self) -> Response:
        """Search apps helper: auto-complete lists."""
        req: SearchAppsAclRequestDTO = SearchAppsAclRequestDTO.Schema().load(data=request.get_json())
        res = search_apps_acl(req)
        return SearchAppsAclResponseDTO.Schema().dump({"acl": res}), 200


class SearchApps(Resource):
    def post(self) -> Response:
        """Search apps."""
        req: SearchAppsRequestDTO = SearchAppsRequestDTO.Schema().load(data=request.get_json())
        res = search_apps(req)
        return SearchAppsResponseDTO.Schema().dump({"apps": res}), 200
