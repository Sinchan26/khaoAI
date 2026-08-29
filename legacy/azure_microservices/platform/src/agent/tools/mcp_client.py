import logging
import httpx
from typing import Dict, Any, List, Optional
from ..core.config import settings

class MCPClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.mcp_base_url).rstrip('/')

    async def search_tomato(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        meal_type: Optional[str] = None,
        max_price: Optional[int] = None,
        is_veg: Optional[bool] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/tomato/search"
        payload = {
            "query": query,
            "location": location,
            "meal_type": meal_type,
            "max_price": max_price,
            "is_veg": is_veg,
            "limit": limit
        }
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=clean_payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logging.error(f"Error calling Tomato MCP tool: {e}")
            return []

    async def search_twiggy(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        meal_type: Optional[str] = None,
        max_price: Optional[int] = None,
        is_veg: Optional[bool] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/twiggy/search"
        payload = {
            "query": query,
            "location": location,
            "meal_type": meal_type,
            "max_price": max_price,
            "is_veg": is_veg,
            "limit": limit
        }
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=clean_payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logging.error(f"Error calling Twiggy MCP tool: {e}")
            return []

mcp_client = MCPClient()
