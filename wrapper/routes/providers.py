"""Swiggy connection and address-selection routes."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.auth import require_current_user
from wrapper.db import get_db_session
from wrapper.models import (
    SwiggyAddressSelection, SwiggyConnectResponse, SwiggyConnectionStatus, UserProfile,
)
from wrapper.providers.swiggy import (
    SwiggyAuthenticationRequired, SwiggyConfigurationError, SwiggyMCPClient, SwiggyProviderError,
    begin_oauth, complete_oauth, connection_token, disconnect, get_connection,
)
from wrapper.routes.config import get_preference_record

router = APIRouter(prefix="/providers/swiggy", tags=["Swiggy"])


@router.get("/status", response_model=SwiggyConnectionStatus)
async def swiggy_status(
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    connection = await get_connection(db, user.id)
    preferences = await get_preference_record(db, user.id)
    expires_at = connection.token_expires_at if connection else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    expired = bool(expires_at and expires_at <= datetime.now(timezone.utc))
    return SwiggyConnectionStatus(
        connected=bool(connection and connection.connected and not expired),
        token_expires_at=expires_at.isoformat() if expires_at else None,
        selected_address_id=preferences.selected_swiggy_address_id,
        selected_address_label=preferences.selected_swiggy_address_label,
        needs_reauthentication=expired,
    )


@router.post("/connect", response_model=SwiggyConnectResponse)
async def connect_swiggy(
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return SwiggyConnectResponse(authorization_url=await begin_oauth(db, user.id))
    except SwiggyConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("/callback", include_in_schema=False)
async def swiggy_callback(
    state_value: str = Query(alias="state"),
    code: str = Query(),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        await complete_oauth(db, state_value, code)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Swiggy connection failed") from exc
    return RedirectResponse(url="/?swiggy=connected", status_code=status.HTTP_302_FOUND)


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_swiggy(
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    await disconnect(db, user.id)


@router.get("/addresses")
async def list_swiggy_addresses(
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        token = connection_token(await get_connection(db, user.id))
        return await SwiggyMCPClient(token, user.id).get_addresses()
    except SwiggyAuthenticationRequired as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except SwiggyProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.put("/address")
async def select_swiggy_address(
    selection: SwiggyAddressSelection,
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        token = connection_token(await get_connection(db, user.id))
        response = await SwiggyMCPClient(token, user.id).get_addresses()
    except SwiggyAuthenticationRequired as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except SwiggyProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    data = response.get("data", response)
    addresses = data.get("addresses", data) if isinstance(data, dict) else data
    addresses = addresses if isinstance(addresses, list) else []
    valid_ids = {str(a.get("addressId") or a.get("id")) for a in addresses if isinstance(a, dict)}
    if selection.address_id not in valid_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select an address returned by Swiggy")
    preferences = await get_preference_record(db, user.id)
    preferences.selected_swiggy_address_id = selection.address_id
    preferences.selected_swiggy_address_label = selection.label
    await db.commit()
    return {"selected": True, "address_id": selection.address_id, "label": selection.label}
