from sqlalchemy import func, select, update

from app.database.repositories.base_repository import BaseRepository
from app.db_models.appointment import Appointment
from app.db_models.knowledge_document import KnowledgeDocument
from app.db_models.project import Project


class ProjectRepository(BaseRepository):
    async def list_by_user(self, user_id: int) -> list[dict[str, int | str]]:
        rows = (
            await self.session.execute(
                select(
                    Project.id,
                    Project.name,
                    func.count(func.distinct(KnowledgeDocument.id)).label("document_count"),
                )
                .outerjoin(KnowledgeDocument, KnowledgeDocument.project_id == Project.id)
                .where(Project.user_id == user_id)
                .group_by(Project.id)
                .order_by(Project.name.asc())
            )
        ).all()

        return [
            {
                "id": row.id,
                "name": row.name,
                "chats": 0,
                "documents": int(row.document_count or 0),
            }
            for row in rows
        ]

    async def create(self, user_id: int, name: str, description: str | None = None) -> Project:
        project = Project(user_id=user_id, name=name, description=description)
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_by_id(self, user_id: int, project_id: int) -> Project | None:
        result = await self.session.execute(
            select(Project)
            .where(Project.id == project_id)
            .where(Project.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def rename(self, project: Project, name: str) -> Project:
        project.name = name
        await self.session.flush()
        return project

    async def delete_with_detach(self, project: Project) -> None:
        await self.session.execute(
            update(Appointment)
            .where(Appointment.project_id == project.id)
            .values(project_id=None)
        )
        await self.session.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.project_id == project.id)
            .values(project_id=None)
        )
        await self.session.delete(project)
        await self.session.flush()
