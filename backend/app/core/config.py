from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"), extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str  # required: no default on purpose, so a secret is never hardcoded
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    RATE_LIMIT_PER_MINUTE: int = 20
    SEED_PASSWORD: str = "Demo@12345"  # demo accounts only

    # Email (Resend). Without RESEND_API_KEY emails are only logged, never sent.
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Tasklane <onboarding@resend.dev>"
    APP_URL: str = "http://localhost:5173"  # base of the links inside emails
    EMAIL_ASYNC: bool = True  # send in a background thread so requests are not slowed down
    RESET_TOKEN_MINUTES: int = 30
    VERIFY_TOKEN_HOURS: int = 24
    # Off by default while the Resend sandbox can only deliver to the account owner; turn on once a domain is verified.
    REQUIRE_EMAIL_VERIFICATION: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
