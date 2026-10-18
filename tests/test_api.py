from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from appsvc import create_app
from appsvc.biz.errors import JukeboxSvcException

CONTAINER_OP = {"container": {"id": "c1", "node_id": "n1"}}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SQLDB_PASSWORD", "test")
    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.mark.unit
class TestApi:
    def test_stop_app(self, client):
        with patch("appsvc.services.jukeboxsvc.stop_container") as stop_container:
            res = client.post("/apps/stop", json=CONTAINER_OP)
        assert res.status_code == 200
        assert stop_container.call_args.args[0].id == "c1"

    def test_validation_error(self, client):
        res = client.post("/apps/pause", json={"container": {}})
        assert res.status_code == 400
        assert res.json()["code"] == 1400

    def test_biz_error(self, client):
        with patch("appsvc.services.jukeboxsvc.pause_container", side_effect=JukeboxSvcException("boom")):
            res = client.post("/apps/pause", json=CONTAINER_OP)
        assert res.status_code == 409
        assert res.json() == {"code": 1409, "message": "boom"}

    def test_unknown_error(self, client):
        with patch("appsvc.services.jukeboxsvc.stop_container", side_effect=RuntimeError):
            res = client.post("/apps/stop", json=CONTAINER_OP)
        assert res.status_code == 500
        assert res.json() == {"code": 1500, "message": "unknown error"}

    def test_search_apps_acl(self, client):
        with patch("appsvc.biz.app.search_apps_acl", return_value=["Doom"]):
            res = client.post("/apps/search/acl", json={"app_name": "doom"})
        assert res.status_code == 200
        assert res.json() == {"acl": ["Doom"]}
