import logging
import httpx
from typing import Dict, Any, Optional
from ..config import settings

class AgentClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.agent_base_url).rstrip('/')

    async def orchestrate(
        self,
        message: str,
        location: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        timeout: float = 25.0
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/orchestrate"
        payload = {
            "message": message,
            "location": location,
            "preferences": preferences or {}
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

agent_client = AgentClient()
