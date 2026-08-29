"""Persistent user preference routes."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.auth import require_current_user
from wrapper.db import get_db_session
from wrapper.db_models import UserPreference
from wrapper.models import UserProfile, UserSettings

router = APIRouter(prefix="/settings", tags=["User Settings"])


def preference_dto(record: UserPreference) -> UserSettings:
    return UserSettings(
        user_id=str(record.user_id), default_location=record.default_location,
        dietary_preference=record.dietary_preference,
        budget_preference=record.budget_preference,
        max_delivery_time=record.max_delivery_time,
        selected_swiggy_address_id=record.selected_swiggy_address_id,
        selected_swiggy_address_label=record.selected_swiggy_address_label,
    )


async def get_preference_record(db: AsyncSession, user_id: str) -> UserPreference:
    record = await db.scalar(select(UserPreference).where(UserPreference.user_id == UUID(user_id)))
    if record is None:
        record = UserPreference(user_id=UUID(user_id))
        db.add(record)
        await db.flush()
    return record


@router.get("", response_model=UserSettings)
async def get_settings(user: UserProfile = Depends(require_current_user), db: AsyncSession = Depends(get_db_session)):
    return preference_dto(await get_preference_record(db, user.id))


@router.put("", response_model=UserSettings)
async def update_settings(
    new_settings: UserSettings,
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    record = await get_preference_record(db, user.id)
    record.default_location = new_settings.default_location.strip()
    record.dietary_preference = new_settings.dietary_preference
    record.budget_preference = new_settings.budget_preference
    record.max_delivery_time = new_settings.max_delivery_time
    # Swiggy address identifiers can only be changed through /providers/swiggy/address,
    # where the ID is verified against get_addresses. Never accept arbitrary IDs here.
    await db.commit()
    await db.refresh(record)
    return preference_dto(record)
