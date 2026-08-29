import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    mcp_base_url: str = os.getenv("MCP_BASE_URL", "http://127.0.0.1:7072")
    default_location: str = os.getenv("DEFAULT_LOCATION", "Salt Lake, Sector V")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
