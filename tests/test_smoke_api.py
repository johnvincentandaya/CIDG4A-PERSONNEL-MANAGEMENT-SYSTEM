from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_smoke(fastapi_app):
    with TestClient(fastapi_app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, dict)
    assert "message" in payload


def test_protected_routes_require_auth(fastapi_app):
    with TestClient(fastapi_app) as client:
        resp = client.get("/api/personnel/")
    assert resp.status_code == 401


def test_personnel_list_smoke(client):
    resp = client.get("/api/personnel/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_bmi_list_smoke(client):
    resp = client.get("/api/bmi/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
