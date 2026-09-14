"""App settings for the MatchCare demo."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MATCHCARE_")

    app_name: str = "MatchCare"
    secret_key: str = "matchcare-demo-secret-not-for-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./matchcare.db"
    seed_on_startup: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173"


settings = Settings()
