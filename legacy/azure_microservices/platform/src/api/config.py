import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "khaoAI Main Gateway API"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "khaoai-super-secret-key-change-in-prod")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    agent_base_url: str = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:7071")
    default_location: str = os.getenv("DEFAULT_LOCATION", "Salt Lake, Sector V")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
