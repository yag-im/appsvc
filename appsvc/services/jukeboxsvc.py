import json
import os

from appsvc.biz.dto import (
    ContainerOpDescr,
    ResumeAppRequestDTO,
)
from appsvc.biz.errors import (
    ContainerNotFoundException,
    JukeboxSvcException,
)
from appsvc.services.dto.jukeboxsvc import (
    ResumeContainerRequestDTO,
    RunContainerRequestDTO,
    RunContainerResponseDTO,
    WsConnDC,
)
from appsvc.services.helpers import get_http_client_session

REQUESTS_TIMEOUT_CONN_READ = (3, 10)
JUKEBOXSVC_URL = os.environ["JUKEBOXSVC_URL"]


def run_container(req: RunContainerRequestDTO) -> RunContainerResponseDTO:
    s = get_http_client_session()
    res = s.post(
        url=f"{JUKEBOXSVC_URL}/containers/run",
        data=json.dumps(RunContainerRequestDTO.Schema().dump(req)),
        headers={"Content-Type": "application/json"},
        timeout=(3, 55),
    )
    if res.status_code != 200:
        raise JukeboxSvcException(res.text)
    return RunContainerResponseDTO.Schema().load(data=res.json())


def pause_container(container: ContainerOpDescr) -> None:
    s = get_http_client_session()
    res = s.post(
        url=f"{JUKEBOXSVC_URL}/nodes/{container.node_id}/containers/{container.id}/pause",
        timeout=REQUESTS_TIMEOUT_CONN_READ,
    )
    if res.status_code != 200:
        raise JukeboxSvcException(res.text)


def resume_container(req: ResumeAppRequestDTO) -> None:
    s = get_http_client_session()
    res = s.post(
        url=f"{JUKEBOXSVC_URL}/nodes/{req.container.node_id}/containers/{req.container.id}/resume",
        data=json.dumps(
            ResumeContainerRequestDTO.Schema().dump(
                ResumeContainerRequestDTO(
                    ws_conn=WsConnDC(
                        id=req.ws_conn.id,
                        consumer_id=req.ws_conn.consumer_id,
                    )
                )
            )
        ),
        headers={"Content-Type": "application/json"},
        timeout=REQUESTS_TIMEOUT_CONN_READ,
    )
    if res.status_code != 200:
        raise JukeboxSvcException(res.text)


def stop_container(container: ContainerOpDescr) -> None:
    s = get_http_client_session()
    res = s.post(
        url=f"{JUKEBOXSVC_URL}/nodes/{container.node_id}/containers/{container.id}/stop",
        timeout=REQUESTS_TIMEOUT_CONN_READ,
    )
    if res.status_code == 410:
        raise ContainerNotFoundException(res.text)
    elif res.status_code != 200:
        raise JukeboxSvcException(res.text)
