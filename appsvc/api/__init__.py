from flask_restful import Api

from appsvc.api.app import (
    GetAppRelease,
    PauseApp,
    ResumeApp,
    RunApp,
    SearchApps,
    SearchAppsAcl,
    StopApp,
)

api = Api()

# setup routing
api.add_resource(GetAppRelease, "/apps/<app_release_uuid>")  # GET
api.add_resource(SearchApps, "/apps/search")  # POST
api.add_resource(SearchAppsAcl, "/apps/search/acl")  # POST
api.add_resource(PauseApp, "/apps/pause")  # POST
api.add_resource(ResumeApp, "/apps/resume")  # POST
api.add_resource(RunApp, "/apps/run")  # POST
api.add_resource(StopApp, "/apps/stop")  # POST
