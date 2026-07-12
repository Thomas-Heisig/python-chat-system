from datetime import datetime

from pydantic import BaseModel


class AuthUser(BaseModel):
	id: int
	username: str
	is_admin: bool
	is_active: bool
	created_at: datetime


class LoginRequest(BaseModel):
	username: str
	password: str


class RegisterRequest(BaseModel):
	username: str
	password: str


class AdminCreateUserRequest(BaseModel):
	username: str
	password: str
	is_admin: bool = False


class AdminCreateUserResponse(BaseModel):
	created: bool
	user: AuthUser


class AdminUpdateUserRequest(BaseModel):
	username: str
	is_admin: bool
	is_active: bool
	password: str | None = None


class AdminUpdateUserResponse(BaseModel):
	updated: bool
	user: AuthUser


class AdminKickUserResponse(BaseModel):
	kicked: bool
	user: AuthUser


class AdminUnlockUserResponse(BaseModel):
	unlocked: bool
	user: AuthUser


class AdminDeleteUserResponse(BaseModel):
	deleted: bool
	target_user_id: int


class AuthResponse(BaseModel):
	user: AuthUser
	access_token: str
	token_type: str = "bearer"


class UserPresenceItem(BaseModel):
	id: int
	username: str
	is_admin: bool
	is_active: bool
	online: bool
	last_seen_at: datetime | None


class UserPresenceListResponse(BaseModel):
	items: list[UserPresenceItem]
