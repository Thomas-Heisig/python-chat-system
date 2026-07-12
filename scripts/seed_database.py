import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from app.startup import initialize_runtime


async def main() -> None:
	stats = await initialize_runtime(run_model_scan=False)
	print(f"Seed completed. inserted={stats['inserted']} updated={stats['updated']}")


if __name__ == "__main__":
	asyncio.run(main())
