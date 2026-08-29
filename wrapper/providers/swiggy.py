"""Read-only Swiggy OAuth and MCP integration.

Only discovery tools are allowed. Cart, payment, confirmation, and ordering
tools are intentionally impossible to call through this client.
"""
from __future__ import annotations

import asyncio
import base64
import contextvars
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.config import settings
from wrapper.db_models import ProviderConnection, UserPreference
from wrapper.log import get_logger

_log = get_logger("provider")
READ_ONLY_TOOLS = frozenset({"get_addresses", "search_menu", "search_restaurants", "get_restaurant_menu"})
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


class SwiggyConfigurationError(RuntimeError):
    pass


class SwiggyAuthenticationRequired(RuntimeError):
    pass


class SwiggyProviderError(RuntimeError):
    pass


def _fernet() -> Fernet:
    if not settings.provider_token_encryption_key:
        raise SwiggyConfigurationError(
            "PROVIDER_TOKEN_ENCRYPTION_KEY is required. Generate one with "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(settings.provider_token_encryption_key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise SwiggyConfigurationError("PROVIDER_TOKEN_ENCRYPTION_KEY is not a valid Fernet key") from exc


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SwiggyConfigurationError("Stored Swiggy token could not be decrypted") from exc


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


async def get_connection(db: AsyncSession, user_id: str) -> ProviderConnection | None:
    return await db.scalar(
        select(ProviderConnection).where(
            ProviderConnection.user_id == UUID(user_id), ProviderConnection.provider == "swiggy"
        )
    )


async def _oauth_metadata(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(
        f"{settings.swiggy_oauth_base_url}/.well-known/oauth-authorization-server"
    )
    response.raise_for_status()
    return response.json()


async def begin_oauth(db: AsyncSession, user_id: str) -> str:
    _fernet()  # fail before creating partial OAuth state
    timeout = settings.swiggy_request_timeout_seconds
    async with httpx.AsyncClient(timeout=timeout) as client:
        metadata = await _oauth_metadata(client)
        redirect_uri = settings.swiggy_redirect_uri
        connection = await get_connection(db, user_id)
        if connection is None:
            connection = ProviderConnection(user_id=UUID(user_id), provider="swiggy")
            db.add(connection)

        client_id = connection.oauth_client_id
        if not client_id:
            registration_endpoint = metadata.get("registration_endpoint") or (
                f"{settings.swiggy_oauth_base_url}/auth/register"
            )
            registration = await client.post(registration_endpoint, json={
                "client_name": "khaoAI Local",
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            })
            registration.raise_for_status()
            client_id = registration.json()["client_id"]

        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(32)
        connection.oauth_client_id = client_id
        connection.oauth_state = state
        connection.code_verifier = verifier
        connection.redirect_uri = redirect_uri
        connection.connected = False
        await db.commit()

        authorization_endpoint = metadata.get("authorization_endpoint") or (
            f"{settings.swiggy_oauth_base_url}/auth/authorize"
        )
        query = urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "mcp:tools mcp:resources mcp:prompts",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        return f"{authorization_endpoint}?{query}"


async def complete_oauth(db: AsyncSession, state: str, code: str) -> ProviderConnection:
    connection = await db.scalar(
        select(ProviderConnection).where(
            ProviderConnection.provider == "swiggy", ProviderConnection.oauth_state == state
        )
    )
    if not connection or not connection.code_verifier or not connection.oauth_client_id:
        raise SwiggyAuthenticationRequired("OAuth state is invalid or expired")
    updated_at = connection.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    if updated_at < datetime.now(timezone.utc) - timedelta(minutes=15):
        raise SwiggyAuthenticationRequired("OAuth state expired; start the connection again")

    async with httpx.AsyncClient(timeout=settings.swiggy_request_timeout_seconds) as client:
        metadata = await _oauth_metadata(client)
        token_endpoint = metadata.get("token_endpoint") or f"{settings.swiggy_oauth_base_url}/auth/token"
        response = await client.post(token_endpoint, data={
            "grant_type": "authorization_code",
            "client_id": connection.oauth_client_id,
            "code": code,
            "redirect_uri": connection.redirect_uri,
            "code_verifier": connection.code_verifier,
        })
        response.raise_for_status()
        payload = response.json()

    access_token = payload.get("access_token")
    if not access_token:
        raise SwiggyAuthenticationRequired("Swiggy did not return an access token")
    connection.encrypted_access_token = encrypt_token(access_token)
    connection.token_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=int(payload.get("expires_in", 5 * 24 * 60 * 60))
    )
    connection.connected = True
    connection.oauth_state = None
    connection.code_verifier = None
    await db.commit()
    return connection


async def disconnect(db: AsyncSession, user_id: str) -> None:
    connection = await get_connection(db, user_id)
    if connection:
        connection.encrypted_access_token = None
        connection.token_expires_at = None
        connection.connected = False
        await db.commit()


def connection_token(connection: ProviderConnection | None) -> str:
    now = datetime.now(timezone.utc)
    if not connection or not connection.connected or not connection.encrypted_access_token:
        raise SwiggyAuthenticationRequired("Connect your Swiggy account before searching")
    expires_at = connection.token_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= now:
        raise SwiggyAuthenticationRequired("Your Swiggy connection expired; reconnect to continue")
    return decrypt_token(connection.encrypted_access_token)


def _parse_mcp_result(result: Any) -> dict[str, Any]:
    if getattr(result, "isError", False) or getattr(result, "is_error", False):
        raise SwiggyProviderError("Swiggy MCP returned an error")
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                value = json.loads(text)
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
    raise SwiggyProviderError("Swiggy MCP returned no structured response")


class SwiggyMCPClient:
    def __init__(self, access_token: str, cache_namespace: str):
        self.access_token = access_token
        self.cache_namespace = cache_namespace

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in READ_ONLY_TOOLS:
            raise PermissionError(f"Swiggy tool '{tool_name}' is not allowed by khaoAI")
        now = time.monotonic()
        if len(_CACHE) > 512:
            for key, value in list(_CACHE.items()):
                if value[0] <= now:
                    _CACHE.pop(key, None)
            while len(_CACHE) > 512:
                oldest = min(_CACHE, key=lambda key: _CACHE[key][0])
                _CACHE.pop(oldest, None)
        cache_key = f"{self.cache_namespace}:{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                from mcp import ClientSession
                from mcp.client.streamable_http import streamablehttp_client

                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with streamablehttp_client(
                    settings.swiggy_mcp_url,
                    headers=headers,
                    timeout=timedelta(seconds=settings.swiggy_request_timeout_seconds),
                ) as streams:
                    read_stream, write_stream = streams[0], streams[1]
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)
                parsed = _parse_mcp_result(result)
                if parsed.get("success") is False:
                    message = (parsed.get("error") or {}).get("message", "Swiggy request failed")
                    raise SwiggyProviderError(message)
                _CACHE[cache_key] = (
                    time.monotonic() + settings.swiggy_cache_ttl_seconds, parsed,
                )
                return parsed
            except SwiggyProviderError:
                raise
            except Exception as exc:
                response = getattr(exc, "response", None)
                if response is not None and getattr(response, "status_code", None) == 401:
                    raise SwiggyAuthenticationRequired("Your Swiggy connection expired; reconnect to continue") from exc
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.25 * (2 ** attempt))
        raise SwiggyProviderError("Swiggy is temporarily unavailable") from last_error

    async def get_addresses(self) -> dict[str, Any]:
        return await self.call_tool("get_addresses", {"page": 1, "pageSize": 10})

    async def search_menu(self, address_id: str, query: str, veg_only: bool = False) -> dict[str, Any]:
        arguments: dict[str, Any] = {"addressId": address_id, "query": query, "offset": 0}
        if veg_only:
            arguments["vegFilter"] = 1
        return await self.call_tool("search_menu", arguments)


@dataclass(frozen=True)
class SwiggyRuntimeContext:
    client: SwiggyMCPClient
    address_id: str
    address_label: str


_runtime_context: contextvars.ContextVar[SwiggyRuntimeContext | None] = contextvars.ContextVar(
    "swiggy_runtime_context", default=None
)


def set_runtime_context(context: SwiggyRuntimeContext):
    return _runtime_context.set(context)


def reset_runtime_context(token) -> None:
    _runtime_context.reset(token)


def current_runtime_context() -> SwiggyRuntimeContext | None:
    return _runtime_context.get()


async def build_runtime_context(db: AsyncSession, user_id: str) -> SwiggyRuntimeContext:
    connection = await get_connection(db, user_id)
    access_token = connection_token(connection)
    preferences = await db.scalar(
        select(UserPreference).where(UserPreference.user_id == UUID(user_id))
    )
    if not preferences or not preferences.selected_swiggy_address_id:
        raise SwiggyAuthenticationRequired("Choose a Swiggy delivery address before searching")
    return SwiggyRuntimeContext(
        client=SwiggyMCPClient(access_token, cache_namespace=user_id),
        address_id=preferences.selected_swiggy_address_id,
        address_label=preferences.selected_swiggy_address_label or "Selected Swiggy address",
    )


def normalize_menu_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data", payload)
    items = data.get("items", []) if isinstance(data, dict) else []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        price = item.get("price")
        if price is None:
            variations = item.get("variations") or []
            variant_prices = [v.get("price") for v in variations if isinstance(v, dict) and v.get("price") is not None]
            price = min(variant_prices) if variant_prices else None
        if price is None:
            continue
        rating_raw = item.get("rating")
        try:
            rating = float(rating_raw) if rating_raw not in (None, "") else None
        except (TypeError, ValueError):
            rating = None
        total_ratings_raw = str(item.get("totalRatings") or "0")
        digits = "".join(ch for ch in total_ratings_raw if ch.isdigit())
        normalized.append({
            "id": str(item.get("menu_item_id") or item.get("id") or secrets.token_hex(8)),
            "restaurant_id": str(item.get("restaurant_id") or ""),
            "restaurant_name": str(item.get("restaurant_name") or "Swiggy restaurant"),
            "platform": "Swiggy",
            "location": "",
            "name": str(item["name"]),
            "price": float(price),
            "meal_type": "",
            "cuisine": "",
            "is_veg": item.get("isVeg"),
            "rating": rating,
            "ratings_count": int(digits or 0),
            "delivery_time_mins": None,
            "distance_km": None,
            "availability": "AVAILABLE" if item.get("inStock", 1) not in (0, False) else "OUT_OF_STOCK",
            "description": str(item.get("description") or ""),
            "image_url": str(item.get("imageUrl") or ""),
            "is_bestseller": bool(item.get("isBestseller")),
        })
    return normalized
