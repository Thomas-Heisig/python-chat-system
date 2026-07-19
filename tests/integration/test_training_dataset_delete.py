from __future__ import annotations

from typing import Any

from app.db_models.training_dataset_file import TrainingDatasetFile
from tests.integration.async_utils import run_async


def test_delete_dataset_removes_registered_files_first(app_client: Any) -> None:
    created = app_client.post(
        "/api/training/datasets",
        json={"user_id": 1, "name": "delete-with-files"},
    )
    assert created.status_code == 200
    dataset_id = int(created.json()["id"])

    async def _add_file_record() -> None:
        from app.database.session import get_session_maker

        async with get_session_maker()() as session:
            session.add(
                TrainingDatasetFile(
                    dataset_id=dataset_id,
                    split="training",
                    file_role="training",
                    relative_path="delete-with-files/training.jsonl",
                    original_name="training.jsonl",
                    sha256="0" * 64,
                    size_bytes=1,
                    record_count=1,
                    status="validated",
                )
            )
            await session.commit()

    run_async(_add_file_record())

    deleted = app_client.delete(f"/api/training/datasets/{dataset_id}?user_id=1")

    assert deleted.status_code == 200
    assert deleted.json() == {
        "deleted": True,
        "dataset_id": dataset_id,
        "deleted_file_records": 1,
    }
    assert app_client.get("/api/training/datasets?user_id=1").json()["items"] == []
