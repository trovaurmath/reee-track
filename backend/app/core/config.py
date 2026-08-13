from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "REEE-Track"
    environment: Literal["development", "test", "demo", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    public_frontend_url: str = "http://localhost:3000"
    seed_demo_data: bool = True

    database_url: str = "sqlite:///./reee_track.db"

    jwt_secret_key: str = Field(
        default="replace-with-at-least-32-random-characters",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    initial_admin_username: str = "admin"
    initial_admin_email: str = "admin@example.invalid"
    initial_admin_full_name: str = "Administrador do sistema"
    initial_admin_password: str = Field(default="change-this-password", min_length=12)

    @field_validator("database_url")
    @classmethod
    def select_psycopg_driver(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def reject_development_secrets_in_production(self) -> "Settings":
        if self.environment in {"demo", "production"}:
            forbidden = {
                "replace-with-at-least-32-random-characters",
                "change-this-password",
            }
            if self.jwt_secret_key in forbidden or self.initial_admin_password in forbidden:
                raise ValueError(
                    "Segredos de desenvolvimento não são permitidos em ambientes públicos"
                )
            if self.environment == "production" and self.seed_demo_data:
                raise ValueError("SEED_DEMO_DATA deve ser false em produção")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
