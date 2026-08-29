import os
import httpx
from typing import Dict, Any, Optional

TOMATO_SERVICE_URL = os.getenv("TOMATO_SERVICE_URL", "http://127.0.0.1:8081")
TWIGGY_SERVICE_URL = os.getenv("TWIGGY_SERVICE_URL", "http://127.0.0.1:8082")

async def fetch_from_simulator(
    base_url: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    # Filter None params
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, params=clean_params)
        response.raise_for_status()
        return response.json()
