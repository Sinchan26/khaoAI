"""Settings / config API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from wrapper.auth import USER_SETTINGS_DB, get_current_user
from wrapper.models import UserProfile, UserSettings

router = APIRouter(prefix="/settings", tags=["User Settings"])


@router.get("", response_model=UserSettings)
def get_settings(user: UserProfile = Depends(get_current_user)):
    user_id = user.id if user else "anonymous"
    if user_id in USER_SETTINGS_DB:
        return USER_SETTINGS_DB[user_id]
    return UserSettings(
        user_id=user_id,
        default_location="Salt Lake, Sector V",
        dietary_preference="all",
        budget_preference="medium",
        max_delivery_time=45,
    )


@router.put("", response_model=UserSettings)
def update_settings(new_settings: UserSettings, user: UserProfile = Depends(get_current_user)):
    user_id = user.id if user else "anonymous"
    new_settings.user_id = user_id
    USER_SETTINGS_DB[user_id] = new_settings
    return new_settings
