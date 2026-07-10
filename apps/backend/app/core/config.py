from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secrets whose placeholder defaults must never survive into a real deployment:
# a leaked jwt/admin secret means forgeable tokens, a leaked internal secret means
# an open internal API. Keyed by field name -> its placeholder value.
_PLACEHOLDER_SECRETS = {
    "jwt_secret": "change-me",
    "admin_jwt_secret": "admin-change-me",
    "internal_api_secret": "change-me-internal-secret",
}


class Settings(BaseSettings):
    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://video_shop:change_me@localhost:5432/video_shop"
    redis_url: str = "redis://localhost:6379/0"

    # Legacy runtime schema sync (create_all + ad-hoc ADD COLUMN) on startup.
    # Alembic migrations are now the source of truth for schema; set to false
    # once `alembic upgrade head` has been run so the app DB user needs no DDL rights.
    db_auto_schema: bool = True

    bot_token: str = ""
    bot_username: str = ""

    telegram_webapp_url: str = ""
    backend_public_url: str = ""
    media_public_url: str = ""
    admin_public_url: str = ""

    jwt_secret: str = "change-me"  # noqa: S105 - placeholder, overridden by .env
    admin_jwt_secret: str = "admin-change-me"  # noqa: S105 - placeholder, overridden by .env
    admin_jwt_ttl_hours: int = 12
    # When true, admins without 2FA get 403 totp_setup_required on every admin
    # endpoint except login and /auth/2fa/*.
    admin_2fa_required: bool = False
    initdata_max_age_seconds: int = 3600
    admin_default_email: str = ""
    admin_default_password: str = ""
    admin_default_password_hash: str = ""
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

    # Cloudflare R2 media storage (S3-compatible). When these are set, admin
    # uploads land in R2 and are served from the CDN at r2_public_base_url;
    # otherwise uploads fall back to the local media volume (dev/tests).
    r2_endpoint_url: str = ""
    r2_bucket: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_public_base_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _reject_placeholder_secrets_outside_dev(self):
        if self.app_env == "development":
            return self
        offenders = [
            name for name, placeholder in _PLACEHOLDER_SECRETS.items()
            if getattr(self, name) == placeholder
        ]
        if offenders:
            raise ValueError(
                f"Refusing to start with app_env={self.app_env!r}: placeholder "
                f"secrets still set ({', '.join(offenders)}). Set them in .env."
            )
        return self


settings = Settings()
