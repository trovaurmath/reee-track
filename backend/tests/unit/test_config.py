import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_render_postgres_url_uses_psycopg_driver() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:password@database:5432/reee_track",
    )

    assert settings.database_url == (
        "postgresql+psycopg://user:password@database:5432/reee_track"
    )


def test_demo_environment_accepts_seed_with_secure_credentials() -> None:
    settings = Settings(
        _env_file=None,
        environment="demo",
        seed_demo_data=True,
        jwt_secret_key="a-secure-demo-secret-with-more-than-32-characters",
        initial_admin_password="a-secure-demo-password",
    )

    assert settings.environment == "demo"
    assert settings.seed_demo_data is True


def test_demo_environment_rejects_development_credentials() -> None:
    with pytest.raises(ValidationError, match="ambientes públicos"):
        Settings(
            _env_file=None,
            environment="demo",
            jwt_secret_key="replace-with-at-least-32-random-characters",
            initial_admin_password="change-this-password",
        )
