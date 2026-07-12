import json

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.knowledge_document import KnowledgeDocument


class KnowledgeRepository(BaseRepository):
	async def list_documents(self, user_id: int, limit: int = 100) -> list[dict[str, str | int]]:
		rows = (
			await self.session.execute(
				select(KnowledgeDocument)
				.where(KnowledgeDocument.user_id == user_id)
				.order_by(KnowledgeDocument.created_at.desc())
				.limit(limit)
			)
		).scalars().all()

		items: list[dict[str, str | int]] = []
		for row in rows:
			position = "Abschnitt"
			relevance = "n/a"
			if row.metadata_json:
				try:
					metadata = json.loads(row.metadata_json)
					position = str(metadata.get("position", position))
					relevance = str(metadata.get("relevance", relevance))
				except (json.JSONDecodeError, TypeError, ValueError):
					pass

			items.append(
				{
					"id": row.id,
					"file": row.file_name,
					"position": position,
					"relevance": relevance,
					"status": row.status,
					"source": row.source or "Upload",
				}
			)

		return items

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
