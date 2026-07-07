"""Auto-translate service (MyMemory): fills every UI language, keeps the source
verbatim, drops rate-limit notices, and fails loudly when nothing comes back.
The MyMemory HTTP GET is mocked."""
import httpx
import pytest

from app.modules.admin_api.translate.service import LANGUAGES, TranslationError, translate_to_all


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _ok(text):
    return _FakeResp({"responseStatus": 200, "responseData": {"translatedText": text}})


async def test_fills_all_languages(monkeypatch):
    async def fake_get(self, url, params=None):
        # echo the target language so we can assert per-language wiring
        tgt = params["langpair"].split("|")[1]
        return _ok(f"[{tgt}]")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    out = await translate_to_all("Популярное", "ru")
    assert out["ru"] == "Популярное"       # source kept exactly
    assert set(out) == set(LANGUAGES)       # nothing missing
    assert out["en"] == "[en]"
    assert out["mo"] == "[ro]"              # Moldovan routed through Romanian


async def test_empty_text_is_noop():
    assert await translate_to_all("   ", "ru") == {}


async def test_rate_limit_notice_is_dropped(monkeypatch):
    async def fake_get(self, url, params=None):
        return _ok("MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(TranslationError):
        await translate_to_all("hi", "en")   # every target dropped -> only source -> error


async def test_unknown_source_defaults_to_en(monkeypatch):
    async def fake_get(self, url, params=None):
        return _ok("x")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    out = await translate_to_all("hello", "zz")  # zz unsupported -> treated as en
    assert out["en"] == "hello"
