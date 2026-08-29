"""Auth service, JWT utilities, and FastAPI auth middleware.

Consolidated from the original:
  - platform/src/api/services/auth_service.py
  - platform/src/api/middleware/auth_middleware.py
  - platform/src/api/utils/security.py
"""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wrapper.log import get_logger
from wrapper.models import (
    TokenResponse,
    UserLogin,
    UserProfile,
    UserRegister,
    UserSettings,
)

_log = get_logger("auth")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "khaoai-super-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# ---------------------------------------------------------------------------
# JWT / Password utilities
# ---------------------------------------------------------------------------

_SALT = "khaoai_secure_salt_2026"


def hash_password(password: str) -> str:
    return hashlib.sha256((password + _SALT).encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

USERS_DB: dict[str, dict] = {}
USER_SETTINGS_DB: dict[str, UserSettings] = {}

# Seed demo user
_demo_id = str(uuid.uuid4())
USERS_DB["demo@khaoai.com"] = {
    "id": _demo_id,
    "email": "demo@khaoai.com",
    "password_hash": hash_password("demo123"),
    "display_name": "Foodie Sinchan",
}
USER_SETTINGS_DB[_demo_id] = UserSettings(
    user_id=_demo_id,
    default_location="Salt Lake, Sector V",
    dietary_preference="all",
    budget_preference="medium",
    max_delivery_time=45,
)
_log.info("Seeded demo user: demo@khaoai.com / demo123")


# ---------------------------------------------------------------------------
# Auth service
# ---------------------------------------------------------------------------

class AuthService:
    @staticmethod
    def register(user_data: UserRegister) -> TokenResponse:
        email = user_data.email.lower().strip()
        if email in USERS_DB:
            _log.warning("Register failed: %s (already exists)", email)
            raise ValueError("Email is already registered")

        user_id = str(uuid.uuid4())
        USERS_DB[email] = {
            "id": user_id,
            "email": email,
            "password_hash": hash_password(user_data.password),
            "display_name": user_data.display_name,
        }
        USER_SETTINGS_DB[user_id] = UserSettings(
            user_id=user_id,
            default_location="Salt Lake, Sector V",
            dietary_preference="all",
            budget_preference="medium",
            max_delivery_time=45,
        )
        token = create_access_token({"sub": user_id, "email": email})
        _log.info("User registered: %s (user_id=%s)", email, user_id)
        return TokenResponse(
            access_token=token,
            user=UserProfile(id=user_id, email=email, display_name=user_data.display_name),
        )

    @staticmethod
    def login(login_data: UserLogin) -> TokenResponse:
        email = login_data.email.lower().strip()
        record = USERS_DB.get(email)
        if not record or not verify_password(login_data.password, record["password_hash"]):
            _log.warning("Login failed: %s (invalid credentials)", email)
            raise ValueError("Invalid email or password")
        token = create_access_token({"sub": record["id"], "email": email})
        _log.info("Login success: %s", email)
        return TokenResponse(
            access_token=token,
            user=UserProfile(
                id=record["id"], email=record["email"], display_name=record["display_name"],
            ),
        )

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[UserProfile]:
        for record in USERS_DB.values():
            if record["id"] == user_id:
                return UserProfile(
                    id=record["id"], email=record["email"], display_name=record["display_name"],
                )
        return None


auth_service = AuthService()


# ---------------------------------------------------------------------------
# FastAPI middleware / dependencies
# ---------------------------------------------------------------------------

_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
) -> Optional[UserProfile]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    return auth_service.get_user_by_id(payload["sub"])


async def require_current_user(
    user: Optional[UserProfile] = Depends(get_current_user),
) -> UserProfile:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
