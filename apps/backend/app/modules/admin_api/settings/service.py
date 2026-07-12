"""Settings admin service - use-case logic."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings as config
from app.models import Base
from app.modules.admin.models import AdminLog, Setting
from app.modules.admin_api.settings.repository import SettingsAdminRepository

# Tables preserved by a full reset: admin accounts (never lock the operator out),
# the settings singleton (pricing/config the admin set up), the migration marker,
# and the Google Drive integration token (a credential, not shop data).
_RESET_KEEP_TABLES = frozenset({"admins", "settings", "alembic_version", "google_drive_tokens"})

# Money-critical bounds. The admin UI enforces the same limits client-side;
# this guards direct API calls (a negative rate or discount cap would corrupt
# every price / overcharge buyers).
_PERCENT_FIELDS = (
    "withdrawal_commission_percent", "max_discount_percent",
    "discount_first_purchase_percent", "discount_bulk_percent", "discount_loyalty_percent",
)
_MIN1_FIELDS = (
    "discount_bulk_min_items", "discount_loyalty_min_items",
    "sub_price_week_stars", "sub_price_month_stars", "sub_price_year_stars",
)


def _validate_pricing_bounds(payload: dict) -> None:
    rate = payload.get("manual_stars_to_usd_rate")
    if rate is not None and float(rate) <= 0:
        raise ValueError("Курс Stars → USD должен быть больше нуля")
    if payload.get("stars_to_usd_mode") not in (None, "auto", "manual"):
        raise ValueError("stars_to_usd_mode: только auto или manual")
    for f in _PERCENT_FIELDS:
        v = payload.get(f)
        if v is not None and not 0 <= int(v) <= 100:
            raise ValueError(f"{f}: допустимо 0–100")
    for f in _MIN1_FIELDS:
        v = payload.get(f)
        if v is not None and int(v) < 1:
            raise ValueError(f"{f}: минимум 1")


class SettingsAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingsAdminRepository(db)

    @staticmethod
    def _with_rate(setting: Setting) -> Setting:
        # expose the built-in fallback rate (a constant, not a DB column) so the
        # admin form can preview USD prices even in "standard" mode
        setting.star_usd_rate = config.star_usd_rate  # ty: ignore[unresolved-attribute] — deliberately dynamic, not a DB column
        return setting

    async def get(self) -> Setting:
        # self-healing singleton: a lost row (fresh DB, partial restore) must
        # not 404-loop the admin settings page — recreate it with defaults
        setting = await self.repo.get_or_create()
        await self.db.commit()
        await self.db.refresh(setting)
        return self._with_rate(setting)

    async def update(self, admin, payload: dict) -> Setting:
        _validate_pricing_bounds(payload)
        setting = await self.repo.get_or_create()
        await self.repo.update(setting, {k: v for k, v in payload.items() if hasattr(setting, k) and k != "id"})
        self.db.add(AdminLog(admin_id=admin.id, action="update_settings", entity_type="settings", entity_id=setting.id))
        await self.db.commit()
        await self.db.refresh(setting)
        return self._with_rate(setting)

    async def reset_all(self, admin) -> dict:
        # Wipe all shop data back to a fresh install. TRUNCATE ... CASCADE clears
        # every table in one shot regardless of FK order; RESTART IDENTITY resets
        # the id sequences so new records start at 1.
        tables = [t.name for t in Base.metadata.sorted_tables if t.name not in _RESET_KEEP_TABLES]
        quoted = ", ".join(f'"{t}"' for t in tables)
        await self.db.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))
        self.db.add(AdminLog(admin_id=admin.id, action="reset_all_data", entity_type="settings", entity_id=1))
        await self.db.commit()
        return {"ok": True, "cleared": tables}