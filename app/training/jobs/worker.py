import asyncio

from app.database.session import get_session_maker
from app.database.repositories.training_job_repository import TrainingJobRepository
from app.settings.service import SettingsService
from app.training.jobs.executor import TrainingJobExecutor


class TrainingWorker:
    def __init__(self, poll_interval_seconds: float = 1.5) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._executor = TrainingJobExecutor()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="training-worker")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        await self._recover_interrupted_jobs()
        while not self._stop_event.is_set():
            job_id = await self._claim_next_job_id()
            if job_id is None:
                await asyncio.sleep(self._poll_interval_seconds)
                continue
            await self._executor.run(job_id)

    async def _recover_interrupted_jobs(self) -> None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = TrainingJobRepository(session)
            await repo.recover_interrupted_jobs()
            await session.commit()

    async def _claim_next_job_id(self) -> int | None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = TrainingJobRepository(session)
            await repo.cancel_pending_queued()
            next_job = await repo.peek_next_queued()
            if next_job is not None:
                settings = SettingsService(session)
                auto_start = await settings.get("training", "auto_start_queue", user_id=next_job.user_id)
                if not bool(auto_start):
                    await session.commit()
                    return None
            job = await repo.claim_next_queued()
            if job is None:
                await session.commit()
                return None
            await session.commit()
            return int(job.id)


training_worker = TrainingWorker()
