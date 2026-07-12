from fastapi import APIRouter, Depends, Header, HTTPException
import asyncio
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.core.auth_token import issue_access_token, verify_access_token
from app.core.security import hash_password, verify_password
from app.database.repositories.user_repository import UserRepository
from app.schemas.user import (
	AdminCreateUserRequest,
	AdminCreateUserResponse,
	AdminDeleteUserResponse,
	AdminKickUserResponse,
	AdminUnlockUserResponse,
	AdminUpdateUserRequest,
	AdminUpdateUserResponse,
	AuthResponse,
	AuthUser,
	LoginRequest,
	RegisterRequest,
	UserPresenceItem,
	UserPresenceListResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_auth_user(user) -> AuthUser:
	return AuthUser(
		id=user.id,
		username=user.username,
		is_admin=user.is_admin,
		is_active=user.is_active,
		created_at=user.created_at,
	)


def _extract_bearer_token(authorization: str | None) -> str | None:
	if not authorization:
		return None
	prefix = "Bearer "
	if not authorization.startswith(prefix):
		return None
	token = authorization[len(prefix):].strip()
	return token or None


async def _require_authenticated_user(
	session: AsyncSession,
	authorization: str | None,
) -> tuple[int, object]:
	token = _extract_bearer_token(authorization)
	if token is None:
		raise HTTPException(status_code=401, detail="Missing bearer token")

	user_id = verify_access_token(token)
	if user_id is None:
		raise HTTPException(status_code=401, detail="Invalid or expired token")

	repo = UserRepository(session)
	user = await repo.get_by_id(user_id)
	if user is None:
		raise HTTPException(status_code=401, detail="Token user not found")
	if not user.is_active:
		raise HTTPException(status_code=403, detail="User is disabled")

	return user_id, user


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(db_session_dependency)) -> AuthResponse:
	username = payload.username.strip()
	password = payload.password.strip()

	if len(username) < 3:
		raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
	if len(password) < 4:
		raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

	repo = UserRepository(session)
	existing = await repo.get_by_username(username)
	if existing is not None:
		raise HTTPException(status_code=409, detail="Username already exists")

	user = await repo.create_user(username=username, password_hash=hash_password(password), is_admin=False)
	await session.commit()
	return AuthResponse(user=_to_auth_user(user), access_token=issue_access_token(user.id))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(db_session_dependency)) -> AuthResponse:
	repo = UserRepository(session)
	username = payload.username.strip()
	user = await repo.get_by_username(username)
	if user is None:
		raise HTTPException(status_code=401, detail="Invalid credentials")
	if not user.is_active:
		raise HTTPException(status_code=403, detail="User is disabled")
	if not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=401, detail="Invalid credentials")

	if not (user.password_hash or "").startswith("pbkdf2_"):
		user.password_hash = hash_password(payload.password)

	await repo.mark_authenticated(user)
	await session.commit()

	return AuthResponse(user=_to_auth_user(user), access_token=issue_access_token(user.id))


@router.get("/me", response_model=AuthResponse)
async def me(
	user_id: int | None = None,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AuthResponse:
	if authorization is not None:
		authenticated_user_id, authenticated_user = await _require_authenticated_user(session, authorization)
		return AuthResponse(user=_to_auth_user(authenticated_user), access_token=issue_access_token(authenticated_user_id))

	if user_id is None:
		raise HTTPException(status_code=400, detail="user_id is required when no bearer token is provided")

	repo = UserRepository(session)
	user = await repo.get_by_id(user_id)
	if user is None:
		raise HTTPException(status_code=404, detail="User not found")
	if not user.is_active:
		raise HTTPException(status_code=403, detail="User is disabled")
	return AuthResponse(user=_to_auth_user(user), access_token=issue_access_token(user.id))


@router.get("/users", response_model=UserPresenceListResponse)
async def list_users(
	online_window_minutes: int = 5,
	session: AsyncSession = Depends(db_session_dependency),
) -> UserPresenceListResponse:
	repo = UserRepository(session)
	rows = await repo.list_with_presence(online_window_minutes=online_window_minutes)
	return UserPresenceListResponse(
		items=[
			UserPresenceItem(
				id=user.id,
				username=user.username,
				is_admin=user.is_admin,
				is_active=user.is_active,
				online=is_online,
				last_seen_at=last_seen_at,
			)
			for user, is_online, last_seen_at in rows
		]
	)


@router.post("/heartbeat")
async def heartbeat(
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, bool]:
	repo = UserRepository(session)
	_authenticated_user_id, user = await _require_authenticated_user(session, authorization)

	updated = False
	for attempt in range(3):
		try:
			await repo.mark_presence_heartbeat(user)
			await session.commit()
			updated = True
			break
		except OperationalError as exc:
			await session.rollback()
			if "database is locked" not in str(exc).lower():
				raise
			if attempt >= 2:
				break
			await asyncio.sleep(0.1 * (2**attempt))

	return {"ok": True, "presence_updated": updated}


@router.post("/admin/users", response_model=AdminCreateUserResponse)
async def admin_create_user(
	payload: AdminCreateUserRequest,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AdminCreateUserResponse:
	repo = UserRepository(session)
	admin_user_id, admin_user = await _require_authenticated_user(session, authorization)
	if not admin_user.is_admin:
		raise HTTPException(status_code=403, detail="Only admins can create users")

	username = payload.username.strip()
	password = payload.password.strip()

	if len(username) < 3:
		raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
	if len(password) < 4:
		raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

	existing = await repo.get_by_username(username)
	if existing is not None:
		raise HTTPException(status_code=409, detail="Username already exists")

	user = await repo.create_user(
		username=username,
		password_hash=hash_password(password),
		is_admin=payload.is_admin,
	)
	await repo.create_user_audit_log(
		actor_user_id=admin_user_id,
		target_user_id=user.id,
		action="user.created",
		details={
			"username": user.username,
			"is_admin": user.is_admin,
			"is_active": user.is_active,
		},
	)
	await session.commit()

	return AdminCreateUserResponse(created=True, user=_to_auth_user(user))


@router.patch("/admin/users/{target_user_id}", response_model=AdminUpdateUserResponse)
async def admin_update_user(
	target_user_id: int,
	payload: AdminUpdateUserRequest,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AdminUpdateUserResponse:
	repo = UserRepository(session)
	admin_user_id, admin_user = await _require_authenticated_user(session, authorization)
	if not admin_user.is_admin:
		raise HTTPException(status_code=403, detail="Only admins can edit users")

	target_user = await repo.get_by_id(target_user_id)
	if target_user is None:
		raise HTTPException(status_code=404, detail="Target user not found")

	username = payload.username.strip()
	if len(username) < 3:
		raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

	existing = await repo.get_by_username(username)
	if existing is not None and existing.id != target_user_id:
		raise HTTPException(status_code=409, detail="Username already exists")

	if target_user.is_admin and (not payload.is_admin or not payload.is_active):
		active_admins = await repo.count_active_admins()
		if active_admins <= 1:
			raise HTTPException(status_code=400, detail="Cannot modify the last active admin")

	password_hash = None
	if payload.password is not None and payload.password.strip():
		password = payload.password.strip()
		if len(password) < 4:
			raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
		password_hash = hash_password(password)

	updated = await repo.update_user_by_admin(
		target_user,
		username=username,
		is_admin=payload.is_admin,
		is_active=payload.is_active,
		password_hash=password_hash,
	)
	await repo.create_user_audit_log(
		actor_user_id=admin_user_id,
		target_user_id=updated.id,
		action="user.updated",
		details={
			"username": updated.username,
			"is_admin": updated.is_admin,
			"is_active": updated.is_active,
			"password_changed": password_hash is not None,
		},
	)
	await session.commit()

	return AdminUpdateUserResponse(updated=True, user=_to_auth_user(updated))


@router.post("/admin/users/{target_user_id}/kick", response_model=AdminKickUserResponse)
async def admin_kick_user(
	target_user_id: int,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AdminKickUserResponse:
	repo = UserRepository(session)
	admin_user_id, admin_user = await _require_authenticated_user(session, authorization)
	if not admin_user.is_admin:
		raise HTTPException(status_code=403, detail="Only admins can kick users")
	if admin_user_id == target_user_id:
		raise HTTPException(status_code=400, detail="You cannot kick yourself")

	target_user = await repo.get_by_id(target_user_id)
	if target_user is None:
		raise HTTPException(status_code=404, detail="Target user not found")

	if target_user.is_admin:
		active_admins = await repo.count_active_admins()
		if active_admins <= 1:
			raise HTTPException(status_code=400, detail="Cannot kick the last active admin")

	updated = await repo.kick_user(target_user)
	await repo.create_user_audit_log(
		actor_user_id=admin_user_id,
		target_user_id=updated.id,
		action="user.kicked",
		details={
			"username": updated.username,
			"is_active": updated.is_active,
		},
	)
	await session.commit()
	return AdminKickUserResponse(kicked=True, user=_to_auth_user(updated))


@router.post("/admin/users/{target_user_id}/unlock", response_model=AdminUnlockUserResponse)
async def admin_unlock_user(
	target_user_id: int,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AdminUnlockUserResponse:
	repo = UserRepository(session)
	admin_user_id, admin_user = await _require_authenticated_user(session, authorization)
	if not admin_user.is_admin:
		raise HTTPException(status_code=403, detail="Only admins can unlock users")

	target_user = await repo.get_by_id(target_user_id)
	if target_user is None:
		raise HTTPException(status_code=404, detail="Target user not found")
	if target_user.username.startswith("__deleted__"):
		raise HTTPException(status_code=400, detail="Soft-deleted users cannot be unlocked")
	if target_user.is_active:
		return AdminUnlockUserResponse(unlocked=True, user=_to_auth_user(target_user))

	updated = await repo.unlock_user(target_user)
	await repo.create_user_audit_log(
		actor_user_id=admin_user_id,
		target_user_id=updated.id,
		action="user.unlocked",
		details={
			"username": updated.username,
			"is_active": updated.is_active,
		},
	)
	await session.commit()
	return AdminUnlockUserResponse(unlocked=True, user=_to_auth_user(updated))


@router.delete("/admin/users/{target_user_id}", response_model=AdminDeleteUserResponse)
async def admin_delete_user(
	target_user_id: int,
	authorization: str | None = Header(default=None),
	session: AsyncSession = Depends(db_session_dependency),
) -> AdminDeleteUserResponse:
	repo = UserRepository(session)
	admin_user_id, admin_user = await _require_authenticated_user(session, authorization)
	if not admin_user.is_admin:
		raise HTTPException(status_code=403, detail="Only admins can delete users")
	if admin_user_id == target_user_id:
		raise HTTPException(status_code=400, detail="You cannot delete yourself")

	target_user = await repo.get_by_id(target_user_id)
	if target_user is None:
		raise HTTPException(status_code=404, detail="Target user not found")

	if target_user.is_admin:
		active_admins = await repo.count_active_admins()
		if active_admins <= 1:
			raise HTTPException(status_code=400, detail="Cannot delete the last active admin")

	await repo.soft_delete_user(target_user)
	await repo.create_user_audit_log(
		actor_user_id=admin_user_id,
		target_user_id=target_user_id,
		action="user.deleted",
		details={
			"username": target_user.username,
		},
	)
	await session.commit()
	return AdminDeleteUserResponse(deleted=True, target_user_id=target_user_id)
