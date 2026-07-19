from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.plugin_idempotency_record import PluginIdempotencyRecord


class PluginIdempotencyRepository(BaseRepository):
    @staticmethod
    def user_scope(user_id: int | None) -> str:
        return str(user_id) if user_id is not None else "anonymous"

    @staticmethod
    def team_scope(team_id: int | None) -> str:
        return str(team_id) if team_id is not None else "no-team"

    async def get_record(
        self,
        *,
        plugin_id: str,
        function_name: str,
        user_scope: str,
        team_scope: str,
        idempotency_key: str,
    ) -> PluginIdempotencyRecord | None:
        statement = (
            select(PluginIdempotencyRecord)
            .where(PluginIdempotencyRecord.plugin_id == plugin_id)
            .where(PluginIdempotencyRecord.function_name == function_name)
            .where(PluginIdempotencyRecord.user_scope == user_scope)
            .where(PluginIdempotencyRecord.team_scope == team_scope)
            .where(PluginIdempotencyRecord.idempotency_key == idempotency_key)
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def create_in_progress(
        self,
        *,
        plugin_id: str,
        function_name: str,
        user_id: int | None,
        team_id: int | None,
        user_scope: str,
        team_scope: str,
        idempotency_key: str,
        arguments_hash: str,
        lease_expires_at: datetime,
    ) -> PluginIdempotencyRecord:
        item = PluginIdempotencyRecord(
            plugin_id=plugin_id,
            function_name=function_name,
            user_id=user_id,
            team_id=team_id,
            user_scope=user_scope,
            team_scope=team_scope,
            idempotency_key=idempotency_key,
            arguments_hash=arguments_hash,
            status="in_progress",
            response_json=None,
            error_code=None,
            error_message=None,
            last_executed_at=None,
            lease_expires_at=lease_expires_at,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def mark_in_progress(
        self,
        item: PluginIdempotencyRecord,
        *,
        arguments_hash: str,
        lease_expires_at: datetime,
    ) -> None:
        item.arguments_hash = arguments_hash
        item.status = "in_progress"
        item.response_json = None
        item.error_code = None
        item.error_message = None
        item.lease_expires_at = lease_expires_at
        await self.session.flush()

    async def mark_completed(self, item: PluginIdempotencyRecord, *, response_json: dict) -> None:
        item.status = "completed"
        item.response_json = response_json
        item.error_code = None
        item.error_message = None
        item.last_executed_at = datetime.now(timezone.utc)
        item.lease_expires_at = None
        await self.session.flush()

    async def mark_failed(self, item: PluginIdempotencyRecord, *, code: str, message: str) -> None:
        item.status = "failed"
        item.error_code = code
        item.error_message = message
        item.last_executed_at = datetime.now(timezone.utc)
        item.lease_expires_at = None
        await self.session.flush()
