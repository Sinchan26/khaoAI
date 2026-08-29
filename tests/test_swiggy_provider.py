from __future__ import annotations

import pytest

from wrapper.providers.swiggy import SwiggyMCPClient, normalize_menu_response


def test_normalize_search_menu_schema() -> None:
    payload = {"success": True, "data": {"items": [
        {
            "name": "Paneer Biryani", "price": 249, "isVeg": True,
            "menu_item_id": "item-1", "restaurant_id": "restaurant-1",
            "restaurant_name": "Biryani House", "rating": "4.6",
            "totalRatings": "1K+", "inStock": 1, "isBestseller": True,
        },
        {"name": "Unavailable", "price": 199, "menu_item_id": "item-2", "inStock": 0},
    ]}}
    items = normalize_menu_response(payload)
    assert items[0]["id"] == "item-1"
    assert items[0]["platform"] == "Swiggy"
    assert items[0]["rating"] == 4.6
    assert items[0]["is_veg"] is True
    assert items[1]["availability"] == "OUT_OF_STOCK"


@pytest.mark.asyncio
async def test_order_and_payment_tools_are_blocked() -> None:
    client = SwiggyMCPClient("never-used", "test")
    for tool in ("update_food_cart", "place_food_order", "confirm_order", "get_payment_options"):
        with pytest.raises(PermissionError):
            await client.call_tool(tool, {})
