from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration. See .env.example for the full list."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:  # pragma: no cover - startup guard
        raise RuntimeError(
            "DATABASE_URL must be set. Copy backend/.env.example to backend/.env "
            "and fill in a real connection string."
        ) from exc
