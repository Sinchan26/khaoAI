from pydantic import BaseModel
from typing import Optional

class UserSettings(BaseModel):
    user_id: Optional[str] = None
    default_location: str = "Salt Lake, Sector V"
    dietary_preference: str = "all" # 'all' | 'veg' | 'non-veg'
    budget_preference: str = "medium" # 'budget' | 'medium' | 'premium'
    max_delivery_time: int = 45
