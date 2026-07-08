"""The `x-lang` header (the client UI language) is authoritative: it flows
through get_current_user, overrides the stored selected_language, and localizes
storefront content per-request. Absent header keeps the stored/account language."""
import hashlib
import hmac
import json
import time
import urllib.parse

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.modules.catalog.models import Product, ProductTranslation

_SLUG = "lang-test-product"


def _init_data(telegram_id: int, language_code: str) -> str:
    user = json.dumps(
        {"id": telegram_id, "first_name": "T", "language_code": language_code},
        separators=(",", ":"),
    )
    fields = {"auth_date": str(int(time.time())), "user": user}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    pairs = [f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k, v in fields.items()]
    pairs.append(f"hash={h}")
    return "&".join(pairs)


@pytest_asyncio.fixture
async def client(db_session):
    if not await db_session.get(Product, 950):
        db_session.add(Product(id=950, slug=_SLUG, status="published", price_stars=100))
        db_session.add(ProductTranslation(product_id=950, language_code="ru", title="РусскийТайтл"))
        db_session.add(ProductTranslation(product_id=950, language_code="en", title="EnglishTitle"))
        db_session.add(ProductTranslation(product_id=950, language_code="de", title="DeutscherTitel"))
        await db_session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _title(client, telegram_id, account_lang, x_lang):
    headers = {"x-telegram-init-data": _init_data(telegram_id, account_lang)}
    if x_lang is not None:
        headers["x-lang"] = x_lang
    resp = await client.get(f"/products/{_SLUG}", headers=headers)
    assert resp.status_code == 200, resp.text[:200]
    return resp.json()["title"]


@pytest.mark.parametrize(
    "telegram_id,account_lang,x_lang,expected",
    [
        (95001, "ru", "en", "EnglishTitle"),   # UI en beats Russian account/stored
        (95002, "ru", "de", "DeutscherTitel"),  # UI de selected, not the stored ru
        (95003, "ru", None, "РусскийТайтл"),    # no header -> stored/account language
    ],
)
async def test_x_lang_header_localizes_content(client, telegram_id, account_lang, x_lang, expected):
    assert await _title(client, telegram_id, account_lang, x_lang) == expected
