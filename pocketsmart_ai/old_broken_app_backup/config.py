from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
app_name: str = "PocketSmart AI"
app_env: str = "development"

```
# Use a strong value from .env in production.
secret_key: str = "change-me"

database_url: str = "sqlite:///./pocketsmart.db"

gemini_api_key: str | None = None
gemini_model: str = "gemini-3.8-flash"
ai_enabled: bool = True

max_upload_mb: int = 5
access_token_expire_minutes: int = 120

allowed_origins: str = (
    "http://127.0.0.1:8000,http://localhost:8000"
)

model_config = SettingsConfigDict(
    env_file=".env",
    extra="ignore",
)

@property
def cors_origins(self) -> list[str]:
    return [
        origin.strip()
        for origin in self.allowed_origins.split(",")
        if origin.strip()
    ]
```

@lru_cache
def get_settings() -> Settings:
return Settings()
