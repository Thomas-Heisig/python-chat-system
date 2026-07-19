from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, select, update

from app.database.repositories.base_repository import BaseRepository
from app.db_models.plugin_confirmation import PluginConfirmation


class PluginConfirmationRepository(BaseRepository):
    async def create_pending(
        self,
        *,
        confirmation_id: str,
        user_id: int,
        team_id: int | None,
        plugin_id: str,
        function_name: str,
        route_kind: str,
        arguments_json: dict,
        arguments_hash: str,
        plugin_settings_json: dict,
        execution_context_json: dict,
        idempotency_key: str | None,
        expires_at: datetime,
    ) -> PluginConfirmation:
        item = PluginConfirmation(
            confirmation_id=confirmation_id,
            user_id=user_id,
            team_id=team_id,
            plugin_id=plugin_id,
            function_name=function_name,
            route_kind=route_kind,
            arguments_json=arguments_json,
            arguments_hash=arguments_hash,
            plugin_settings_json=plugin_settings_json,
            execution_context_json=execution_context_json,
            idempotency_key=idempotency_key,
            status="pending",
            expires_at=expires_at,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_confirmation_id(self, confirmation_id: str) -> PluginConfirmation | None:
        statement = (
            select(PluginConfirmation)
            .where(PluginConfirmation.confirmation_id == confirmation_id)
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def claim_pending_for_execution(
        self,
        *,
        confirmation_id: str,
        user_id: int,
        team_id: int | None,
        now: datetime,
    ) -> PluginConfirmation | None:
        if team_id is None:
            team_condition = PluginConfirmation.team_id.is_(None)
        else:
            team_condition = PluginConfirmation.team_id == team_id

        statement = (
            update(PluginConfirmation)
            .where(
                and_(
                    PluginConfirmation.confirmation_id == confirmation_id,
                    PluginConfirmation.user_id == user_id,
                    team_condition,
                    PluginConfirmation.status == "pending",
                    PluginConfirmation.expires_at >= now,
                )
            )
            .values(status="executing")
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(statement)
        if (result.rowcount or 0) != 1:
            return None
        await self.session.flush()
        return await self.get_by_confirmation_id(confirmation_id)

    async def mark_rejected(self, item: PluginConfirmation) -> None:
        item.status = "rejected"
        item.decided_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def mark_expired(self, item: PluginConfirmation) -> None:
        item.status = "expired"
        item.decided_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def mark_executed_success(self, item: PluginConfirmation, result: dict) -> None:
        item.status = "confirmed"
        item.decided_at = datetime.now(timezone.utc)
        item.result_json = result
        item.error_code = None
        item.error_message = None
        await self.session.flush()

    async def mark_executed_failure(self, item: PluginConfirmation, *, code: str, message: str) -> None:
        item.status = "failed"
        item.decided_at = datetime.now(timezone.utc)
        item.error_code = code
        item.error_message = message
        await self.session.flush()
