import json

from sqlalchemy import or_, select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.knowledge_document import KnowledgeDocument


class KnowledgeRepository(BaseRepository):
	def _serialize_document_row(self, row: KnowledgeDocument) -> dict[str, object]:
		position = "Abschnitt"
		relevance = "n/a"
		if row.metadata_json:
			try:
				metadata = json.loads(row.metadata_json)
				position = str(metadata.get("position", position))
				relevance = str(metadata.get("relevance", relevance))
			except (json.JSONDecodeError, TypeError, ValueError):
				pass

		return {
			"id": row.id,
			"file": row.file_name,
			"position": position,
			"relevance": relevance,
			"status": row.status,
			"source": row.source or "Upload",
			"project_id": row.project_id,
		}

	async def list_documents(self, user_id: int, limit: int = 100) -> list[dict[str, object]]:
		rows = (
			await self.session.execute(
				select(KnowledgeDocument)
				.where(KnowledgeDocument.user_id == user_id)
				.order_by(KnowledgeDocument.created_at.desc())
				.limit(limit)
			)
		).scalars().all()

		return [self._serialize_document_row(row) for row in rows]

	async def list_documents_for_scope(
		self,
		*,
		user_id: int,
		project_ids: list[int],
		include_unassigned: bool,
		limit: int = 200,
	) -> list[dict[str, object]]:
		query = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)

		if project_ids:
			if include_unassigned:
				query = query.where(
					or_(
						KnowledgeDocument.project_id.in_(project_ids),
						KnowledgeDocument.project_id.is_(None),
					)
				)
			else:
				query = query.where(KnowledgeDocument.project_id.in_(project_ids))
		elif include_unassigned:
			query = query.where(KnowledgeDocument.project_id.is_(None))
		else:
			return []

		rows = (
			await self.session.execute(
				query
				.order_by(KnowledgeDocument.created_at.desc())
				.limit(limit)
			)
		).scalars().all()

		return [self._serialize_document_row(row) for row in rows]

	async def create_document(
		self,
		user_id: int,
		file_name: str,
		source: str,
		status: str,
		metadata: dict[str, str] | None = None,
		project_id: int | None = None,
	) -> KnowledgeDocument:
		metadata_json = json.dumps(metadata) if metadata else None
		item = KnowledgeDocument(
			user_id=user_id,
			file_name=file_name,
			source=source,
			status=status,
			metadata_json=metadata_json,
			project_id=project_id,
		)
		self.session.add(item)
		await self.session.flush()
		return item

	async def delete_seed_mock_documents(self, user_id: int) -> int:
		rows = (
			await self.session.execute(
				select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)
			)
		).scalars().all()

		removed = 0
		for row in rows:
			source = str(row.source or "").strip().lower()
			name = str(row.file_name or "").strip().lower()
			if source == "seed_mock":
				await self.session.delete(row)
				removed += 1
				continue
			if source == "upload" and name in {"angebot_klaener.pdf", "materialliste_lemwerder.docx"}:
				await self.session.delete(row)
				removed += 1

		if removed:
			await self.session.flush()
		return removed

	async def list_documents_for_projects(
		self,
		user_id: int,
		project_ids: list[int],
		limit: int = 500,
	) -> list[KnowledgeDocument]:
		if not project_ids:
			return []

		rows = (
			await self.session.execute(
				select(KnowledgeDocument)
				.where(KnowledgeDocument.user_id == user_id)
				.where(KnowledgeDocument.project_id.in_(project_ids))
				.order_by(KnowledgeDocument.created_at.desc())
				.limit(limit)
			)
		).scalars().all()

		return list(rows)

	async def get_document_by_id(self, user_id: int, document_id: int) -> KnowledgeDocument | None:
		row = (
			await self.session.execute(
				select(KnowledgeDocument)
				.where(KnowledgeDocument.user_id == user_id)
				.where(KnowledgeDocument.id == document_id)
			)
		).scalar_one_or_none()
		return row

	async def assign_document_project(
		self,
		document: KnowledgeDocument,
		project_id: int | None,
	) -> KnowledgeDocument:
		document.project_id = project_id
		await self.session.flush()
		return document
