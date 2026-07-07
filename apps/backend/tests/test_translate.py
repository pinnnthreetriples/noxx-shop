"""Auto-translate service: fills every UI language, keeps the source verbatim,
and fails loudly (not silently) when misconfigured. Gemini HTTP is mocked."""
import json

import httpx
import pytest

from app.core.config import settings
from app.modules.admin_api.translate.service import LANGUAGES, TranslationError, translate_to_all


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _gemini(mapping):
    return {"candidates": [{"content": {"parts": [{"text": json.dumps(mapping)}]}}]}


async def test_fills_all_languages(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    mapping = {c: f"{c}-text" for c in LANGUAGES if c != "ru"}

    async def fake_post(self, url, **kwargs):
        return _FakeResp(_gemini(mapping))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    out = await translate_to_all("Привет", "ru")
    assert out["ru"] == "Привет"          # source kept exactly
    assert set(out) == set(LANGUAGES)      # nothing missing
    assert out["en"] == "en-text"


async def test_empty_text_is_noop():
    assert await translate_to_all("   ", "ru") == {}


async def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(TranslationError):
        await translate_to_all("hi", "en")


async def test_unknown_source_defaults_to_en(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    async def fake_post(self, url, **kwargs):
        return _FakeResp(_gemini({c: c for c in LANGUAGES if c != "en"}))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    out = await translate_to_all("hello", "zz")  # zz not supported -> treated as en
    assert out["en"] == "hello"
