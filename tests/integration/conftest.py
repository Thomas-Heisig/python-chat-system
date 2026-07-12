from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

def _reset_model_manager_state() -> None:
    from app.models.manager import model_manager

    backend = model_manager.active_backend
    unload = getattr(backend, "unload", None)
    if callable(unload):
        unload()

    model_manager.active_backend = None
    model_manager.active_model_id = None
    model_manager.active_backend_name = None


@pytest.fixture
def app_client(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "integration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file.as_posix()}")

    from app.core.config import get_config
    from app.database import connection as db_connection
    from app.database import session as db_session

    get_config.cache_clear()
    db_connection._engine = None
    db_session._session_maker = None

    _reset_model_manager_state()

    from app.main import app

    with TestClient(app) as client:
        yield client

    _reset_model_manager_state()
    db_connection._engine = None
    db_session._session_maker = None
    get_config.cache_clear()
