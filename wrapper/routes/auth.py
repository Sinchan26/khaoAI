"""Auth API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.auth import auth_service, require_current_user
from wrapper.db import get_db_session
from wrapper.models import TokenResponse, UserLogin, UserProfile, UserRegister

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, session: AsyncSession = Depends(get_db_session)):
    try:
        return await auth_service.register(data, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSession = Depends(get_db_session)):
    try:
        return await auth_service.login(data, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(user: UserProfile = Depends(require_current_user)):
    return user
