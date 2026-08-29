"""Database-backed authentication, Argon2 passwords, and JWT dependencies."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.config import settings
from wrapper.db import get_db_session
from wrapper.db_models import User, UserPreference
from wrapper.log import get_logger
from wrapper.models import TokenResponse, UserLogin, UserProfile, UserRegister

_log = get_logger("auth")
_password_hasher = PasswordHasher()
_security = HTTPBearer(auto_error=False)
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def user_profile(record: User) -> UserProfile:
    return UserProfile(id=str(record.id), email=record.email, display_name=record.display_name)


class AuthService:
    async def register(self, data: UserRegister, session: AsyncSession) -> TokenResponse:
        email = data.email.lower().strip()
        if await session.scalar(select(User).where(User.email == email)):
            raise ValueError("Email is already registered")
        record = User(
            email=email,
            password_hash=hash_password(data.password),
            display_name=data.display_name.strip(),
        )
        record.preferences = UserPreference(
            default_location=settings.default_location,
            dietary_preference="all",
            budget_preference="medium",
            max_delivery_time=45,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        profile = user_profile(record)
        _log.info("User registered (user_id=%s)", record.id)
        return TokenResponse(
            access_token=create_access_token({"sub": str(record.id), "email": record.email}),
            user=profile,
        )

    async def login(self, data: UserLogin, session: AsyncSession) -> TokenResponse:
        email = data.email.lower().strip()
        record = await session.scalar(select(User).where(User.email == email))
        if not record or not record.is_active or not verify_password(data.password, record.password_hash):
            _log.warning("Login failed")
            raise ValueError("Invalid email or password")
        return TokenResponse(
            access_token=create_access_token({"sub": str(record.id), "email": record.email}),
            user=user_profile(record),
        )

    async def get_user_by_id(self, user_id: str, session: AsyncSession) -> UserProfile | None:
        try:
            parsed_id = UUID(user_id)
        except ValueError:
            return None
        record = await session.get(User, parsed_id)
        if not record or not record.is_active:
            return None
        return user_profile(record)


auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    session: AsyncSession = Depends(get_db_session),
) -> UserProfile | None:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        return None
    return await auth_service.get_user_by_id(payload["sub"], session)


async def require_current_user(user: UserProfile | None = Depends(get_current_user)) -> UserProfile:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def authenticate_token(token: str, session: AsyncSession) -> UserProfile | None:
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    return await auth_service.get_user_by_id(payload["sub"], session)
