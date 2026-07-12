from datetime import timezone

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.appointment import Appointment


class AppointmentRepository(BaseRepository):
    async def list_by_user(self, user_id: int, limit: int = 50) -> list[dict[str, str | int]]:
        rows = (
            await self.session.execute(
                select(Appointment)
                .where(Appointment.user_id == user_id)
                .order_by(Appointment.due_at.asc().nulls_last(), Appointment.id.asc())
                .limit(limit)
            )
        ).scalars().all()

        items: list[dict[str, str | int]] = []
        for row in rows:
            if row.due_at is not None:
                due_at = row.due_at
                if due_at.tzinfo is None:
                    due_at = due_at.replace(tzinfo=timezone.utc)
                date_label = due_at.astimezone(timezone.utc).strftime("%d.%m")
            else:
                date_label = "Ohne Datum"

            items.append({"id": row.id, "date": date_label, "title": row.title, "state": row.status})

        return items

    async def create(
        self,
        user_id: int,
        title: str,
        status: str = "Vorgeschlagen",
        project_id: int | None = None,
        conversation_id: int | None = None,
    ) -> Appointment:
        item = Appointment(
            user_id=user_id,
            title=title,
            status=status,
            project_id=project_id,
            conversation_id=conversation_id,
        )
        self.session.add(item)
        await self.session.flush()
        return item
