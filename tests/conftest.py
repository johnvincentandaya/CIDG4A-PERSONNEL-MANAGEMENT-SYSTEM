from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest
from pytest import MonkeyPatch


def _ensure_backend_on_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    backend_dir_str = str(backend_dir)
    if backend_dir_str not in sys.path:
        sys.path.insert(0, backend_dir_str)


def _purge_backend_modules() -> None:
    # Ensure environment-variable based config (e.g. DATABASE_URL) is read fresh.
    for name in list(sys.modules):
        if name == "main" or name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)


@pytest.fixture(scope="session")
def fastapi_app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[object]:
    _ensure_backend_on_sys_path()

    data_dir = tmp_path_factory.mktemp("data")
    db_path = data_dir / "test.db"
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    mp = MonkeyPatch()
    mp.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    mp.setenv("UPLOADS_DIR", str(uploads_dir))
    mp.setenv("APP_PASSWORD", "test-password")
    mp.setenv("SESSION_SECRET", "test-session-secret")

    _purge_backend_modules()
    import main  # type: ignore

    importlib.reload(main)
    try:
        yield main.app
    finally:
        mp.undo()


@pytest.fixture()
def client(fastapi_app):
    from fastapi.testclient import TestClient

    with TestClient(fastapi_app) as c:
        res = c.post("/api/auth/login", json={"password": os.environ["APP_PASSWORD"]})
        assert res.status_code == 200
        yield c
