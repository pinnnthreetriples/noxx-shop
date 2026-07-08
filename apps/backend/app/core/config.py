from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://video_shop:change_me@localhost:5432/video_shop"
    redis_url: str = "redis://localhost:6379/0"

    bot_token: str = ""
    bot_username: str = ""

    telegram_webapp_url: str = ""
    backend_public_url: str = ""
    media_public_url: str = ""
    admin_public_url: str = ""

    jwt_secret: str = "change-me"  # noqa: S105 - placeholder, overridden by .env
    admin_jwt_secret: str = "admin-change-me"  # noqa: S105 - placeholder, overridden by .env
    initdata_max_age_seconds: int = 86400
    admin_default_email: str = ""
    admin_default_password: str = ""
    admin_default_telegram_id: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    max_discount_percent: int = 50
    default_language: str = "en"
    internal_api_url: str = "http://backend:8000"
    internal_api_secret: str = "change-me-internal-secret"  # noqa: S105 - placeholder, overridden by .env

    # OrbChain crypto payment gateway
    orbchain_api_key: str = ""
    orbchain_api_base: str = "https://orbchain.io"
    orbchain_webhook_secret: str = ""
    # 1 in-app "star" of price ≈ this many USD when invoicing crypto
    star_usd_rate: float = 0.02

    # Sentry error monitoring. Empty = disabled (no-op), so local/dev stays silent.
    sentry_dsn: str = ""

    # MyMemory admin auto-translation. Keyless; an optional contact email raises
    # the free daily limit (~5k -> ~50k words/day). Not a secret.
    mymemory_email: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
