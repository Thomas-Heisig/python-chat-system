from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.user_audit_log import UserAuditLog
from app.db_models.user import User


class UserRepository(BaseRepository):
	@staticmethod
	def _normalize_utc_naive(value: datetime | None) -> datetime | None:
		if not isinstance(value, datetime):
			return None
		if value.tzinfo is None:
			return value
		return value.astimezone(timezone.utc).replace(tzinfo=None)

	async def get_by_id(self, user_id: int) -> User | None:
		result = await self.session.execute(select(User).where(User.id == user_id))
		return result.scalar_one_or_none()

	async def get_by_username(self, username: str) -> User | None:
		normalized = username.strip().lower()
		result = await self.session.execute(select(User).where(func.lower(User.username) == normalized))
		return result.scalar_one_or_none()

	async def count_active_admins(self) -> int:
		result = await self.session.execute(
			select(func.count(User.id)).where(User.is_admin.is_(True), User.is_active.is_(True))
		)
		return int(result.scalar() or 0)

	async def create_user(self, username: str, password_hash: str, is_admin: bool = False) -> User:
		user = User(
			username=username,
			password_hash=password_hash,
			is_active=True,
			is_admin=is_admin,
		)
		self.session.add(user)
		await self.session.flush()
		return user

	async def update_user_by_admin(
		self,
		user: User,
		*,
		username: str,
		is_admin: bool,
		is_active: bool,
		password_hash: str | None = None,
	) -> User:
		user.username = username
		user.is_admin = is_admin
		user.is_active = is_active
		if password_hash is not None:
			user.password_hash = password_hash
		await self.session.flush()
		return user

	async def kick_user(self, user: User) -> User:
		# Deactivating the account forces bearer-token authenticated requests to fail immediately.
		user.is_active = False
		await self.session.flush()
		return user

	async def unlock_user(self, user: User) -> User:
		user.is_active = True
		await self.session.flush()
		return user

	async def soft_delete_user(self, user: User) -> User:
		user.is_active = False
		user.is_admin = False
		user.password_hash = None
		user.username = f"__deleted__{user.id}"
		await self.session.flush()
		return user

	async def create_user_audit_log(
		self,
		*,
		actor_user_id: int,
		target_user_id: int,
		action: str,
		details: dict[str, object],
	) -> UserAuditLog:
		audit = UserAuditLog(
			actor_user_id=actor_user_id,
			target_user_id=target_user_id,
			action=action,
			details=details,
		)
		self.session.add(audit)
		await self.session.flush()
		return audit

	async def mark_authenticated(self, user: User) -> None:
		# Keep an explicit login event so presence does not depend on generic profile updates.
		user.updated_at = datetime.now(timezone.utc)
		self.session.add(
			UserAuditLog(
				actor_user_id=user.id,
				target_user_id=user.id,
				action="user.login",
				details={"username": user.username},
			)
		)
		await self.session.flush()

	async def mark_presence_heartbeat(self, user: User) -> None:
		now = datetime.now(timezone.utc)
		last_seen = self._normalize_utc_naive(user.updated_at)
		now_naive = now.replace(tzinfo=None)
		if last_seen is not None and (now_naive - last_seen) < timedelta(seconds=30):
			return

		user.updated_at = now
		self.session.add(
			UserAuditLog(
				actor_user_id=user.id,
				target_user_id=user.id,
				action="user.heartbeat",
				details={"username": user.username},
			)
		)
		await self.session.flush()

	async def ensure_default_user(self, user_id: int = 1) -> User:
		existing = await self.get_by_id(user_id)
		if existing is not None:
			return existing

		username_candidate = f"local-user-{user_id}"
		suffix = 1
		while await self.get_by_username(username_candidate) is not None:
			username_candidate = f"local-user-{user_id}-{suffix}"
			suffix += 1

		user = User(
			id=user_id,
			username=username_candidate,
			email=None,
			password_hash=None,
			is_active=True,
			is_admin=(user_id == 1),
		)
		self.session.add(user)
		await self.session.flush()
		return user

	async def list_with_presence(self, online_window_minutes: int = 5) -> list[tuple[User, bool, datetime | None]]:
		# SQLite commonly returns naive datetimes; compare against naive UTC to avoid TypeError.
		cutoff_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=max(1, online_window_minutes))

		login_subquery = (
			select(
				UserAuditLog.target_user_id.label("user_id"),
				func.max(UserAuditLog.created_at).label("last_seen_at"),
			)
			.where(UserAuditLog.action.in_(["user.login", "user.heartbeat"]))
			.group_by(UserAuditLog.target_user_id)
			.subquery()
		)

		result = await self.session.execute(
			select(User, login_subquery.c.last_seen_at)
			.outerjoin(login_subquery, login_subquery.c.user_id == User.id)
			.where(~User.username.like("__deleted__%"))
			.order_by(User.username.asc())
		)

		items: list[tuple[User, bool, datetime | None]] = []
		for user, last_seen_at in result.all():
			normalized_last_seen = self._normalize_utc_naive(last_seen_at)
			is_online = bool(user.is_active and normalized_last_seen is not None and normalized_last_seen >= cutoff_utc_naive)
			items.append((user, is_online, normalized_last_seen))

		return items
