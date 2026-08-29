import uuid
from typing import Dict, Optional
from ..models.auth import UserRegister, UserLogin, UserProfile, TokenResponse
from ..models.settings import UserSettings
from ..utils.security import hash_password, verify_password, create_access_token

# In-memory storage for users and user settings
USERS_DB: Dict[str, dict] = {}
USER_SETTINGS_DB: Dict[str, UserSettings] = {}

# Seed default demo user
demo_id = str(uuid.uuid4())
USERS_DB["demo@khaoai.com"] = {
    "id": demo_id,
    "email": "demo@khaoai.com",
    "password_hash": hash_password("demo123"),
    "display_name": "Foodie Sinchan"
}
USER_SETTINGS_DB[demo_id] = UserSettings(
    user_id=demo_id,
    default_location="Salt Lake, Sector V",
    dietary_preference="all",
    budget_preference="medium",
    max_delivery_time=45
)

class AuthService:
    @staticmethod
    def register(user_data: UserRegister) -> TokenResponse:
        email = user_data.email.lower().strip()
        if email in USERS_DB:
            raise ValueError("Email is already registered")

        user_id = str(uuid.uuid4())
        hashed = hash_password(user_data.password)

        user_record = {
            "id": user_id,
            "email": email,
            "password_hash": hashed,
            "display_name": user_data.display_name
        }
        USERS_DB[email] = user_record

        # Default settings
        USER_SETTINGS_DB[user_id] = UserSettings(
            user_id=user_id,
            default_location="Salt Lake, Sector V",
            dietary_preference="all",
            budget_preference="medium",
            max_delivery_time=45
        )

        token = create_access_token({"sub": user_id, "email": email})
        return TokenResponse(
            access_token=token,
            user=UserProfile(id=user_id, email=email, display_name=user_data.display_name)
        )

    @staticmethod
    def login(login_data: UserLogin) -> TokenResponse:
        email = login_data.email.lower().strip()
        user_record = USERS_DB.get(email)
        if not user_record or not verify_password(login_data.password, user_record["password_hash"]):
            raise ValueError("Invalid email or password")

        token = create_access_token({"sub": user_record["id"], "email": email})
        return TokenResponse(
            access_token=token,
            user=UserProfile(
                id=user_record["id"],
                email=user_record["email"],
                display_name=user_record["display_name"]
            )
        )

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[UserProfile]:
        for record in USERS_DB.values():
            if record["id"] == user_id:
                return UserProfile(
                    id=record["id"],
                    email=record["email"],
                    display_name=record["display_name"]
                )
        return None

auth_service = AuthService()
