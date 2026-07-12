import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.startup import initialize_runtime


async def _init_only(run_scan: bool) -> None:
    stats = await initialize_runtime(run_model_scan=run_scan)
    print(
        "Runtime initialized: "
        f"discovered={stats['discovered']} inserted={stats['inserted']} updated={stats['updated']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Start Kernschmiede")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--skip-model-scan", action="store_true")
    args = parser.parse_args()

    run_scan = not args.skip_model_scan
    if args.init_only:
        asyncio.run(_init_only(run_scan=run_scan))
        return

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
