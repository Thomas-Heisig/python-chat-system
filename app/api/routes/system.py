from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import platform
import socket
import sys
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.core.config import get_config
from app.models.manager import model_manager
from app.settings.service import SettingsService

router = APIRouter(prefix="/api/system", tags=["system"])


def _read_listening_ports() -> list[dict[str, Any]]:
	entries: list[dict[str, Any]] = []
	try:
		import psutil

		for connection in psutil.net_connections(kind="inet"):
			if connection.status != "LISTEN" or connection.laddr is None:
				continue

			host, port = connection.laddr
			entries.append(
				{
					"host": host,
					"port": port,
					"pid": connection.pid,
				}
			)
	except Exception:
		pass

	deduplicated = {
		(entry["host"], entry["port"], entry["pid"]): entry for entry in entries
	}
	return sorted(deduplicated.values(), key=lambda item: int(item["port"]))


@router.get("/diagnostics")
async def diagnostics(session: AsyncSession = Depends(db_session_dependency)) -> dict[str, Any]:
	config = get_config()
	settings_service = SettingsService(session)
	model_base_directories_raw = await settings_service.get("model", "base_directories")

	model_base_directories = (
		[str(item) for item in model_base_directories_raw if isinstance(item, (str, int, float))]
		if isinstance(model_base_directories_raw, list)
		else []
	)

	database_url = config.database_url
	database_path = None
	sqlite_prefix = "sqlite+aiosqlite:///"
	if database_url.startswith(sqlite_prefix):
		raw_path = database_url[len(sqlite_prefix) :]
		database_path = str(Path(raw_path).resolve(strict=False))

	backend_status = {
		"service_name": config.app_name,
		"environment": config.app_env,
		"hostname": socket.gethostname(),
		"active_model_id": model_manager.active_model_id,
		"model_loaded": model_manager.active_backend is not None,
		"active_backend": model_manager.active_backend_name,
		"database_status": "ok",
	}

	return {
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"backend_status": backend_status,
		"python": {
			"version": sys.version,
			"executable": sys.executable,
			"platform": platform.platform(),
			"prefix": sys.prefix,
			"base_prefix": sys.base_prefix,
		},
		"cuda": {
			"available": model_manager._gpu_available(),
		},
		"ports": {
			"listening": _read_listening_ports(),
		},
		"paths": {
			"cwd": os.getcwd(),
			"database_url": database_url,
			"database_path": database_path,
			"model_base_directories": model_base_directories,
		},
	}


@router.get("/diagnostics/export")
async def diagnostics_export(session: AsyncSession = Depends(db_session_dependency)) -> JSONResponse:
	payload = await diagnostics(session)
	timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
	headers = {
		"Content-Disposition": f'attachment; filename="diagnostics-{timestamp}.json"',
		"Cache-Control": "no-store",
	}
	return JSONResponse(content=payload, headers=headers)
