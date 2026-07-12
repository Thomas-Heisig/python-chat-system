import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.session import get_session_maker
from app.models.scanner import ModelScanner
from app.settings.service import SettingsService


async def main() -> None:
    scanner = ModelScanner()
    session_maker = get_session_maker()
    async with session_maker() as session:
        settings = SettingsService(session)
        dirs = await settings.get("model", "base_directories")
        models = scanner.scan_directories([str(x) for x in dirs])
        print(f"Discovered: {len(models)}")
        for model in models:
            print(model)


if __name__ == "__main__":
    asyncio.run(main())
