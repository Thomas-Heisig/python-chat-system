import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.session import get_session_maker
from app.models.scanner import ModelScanner
from app.settings.service import SettingsService


def _safe_model_summary(model: object) -> str:
    name = str(getattr(model, "name", "unknown"))
    backend = str(getattr(model, "backend", "unknown"))
    model_type = str(getattr(model, "model_type", "unknown"))
    model_format = str(getattr(model, "model_format", "unknown"))
    path_value = str(getattr(model, "model_path", ""))
    model_path = Path(path_value).name if path_value else ""
    return json.dumps(
        {
            "name": name,
            "backend": backend,
            "model_type": model_type,
            "model_format": model_format,
            "model_path": model_path,
        },
        ensure_ascii=True,
    )


async def main() -> None:
    scanner = ModelScanner()
    session_maker = get_session_maker()
    async with session_maker() as session:
        settings = SettingsService(session)
        dirs = await settings.get("model", "base_directories")
        models = scanner.scan_directories([str(x) for x in dirs])
        print(f"Discovered: {len(models)}")
        for model in models:
            print(_safe_model_summary(model))


if __name__ == "__main__":
    asyncio.run(main())
