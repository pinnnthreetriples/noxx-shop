"""Admin content auto-translation via MyMemory (free, keyless, no billing).

The owner writes a title/description in one language; this fills the rest.
MyMemory needs no API key. An optional contact email (settings.mymemory_email)
raises the free daily limit from ~5k to ~50k words/day.
"""
import asyncio
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

# The app's UI languages (must match the miniapp language switcher). No `es`.
LANGUAGES: Dict[str, str] = {
    "en": "English",
    "ru": "Russian",
    "de": "German",
    "el": "Greek",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "mo": "Moldovan",
    "sr": "Serbian",
    "tr": "Turkish",
}

# MyMemory codes. Moldovan isn't a MyMemory language — it's Romanian, so map it.
_MM = {"en": "en", "ru": "ru", "de": "de", "el": "el", "ro": "ro",
       "bg": "bg", "mo": "ro", "sr": "sr", "tr": "tr"}

_ENDPOINT = "https://api.mymemory.translated.net/get"


class TranslationError(RuntimeError):
    """Auto-translation could not be produced (upstream error, quota, bad output)."""


async def _one(client: httpx.AsyncClient, text: str, src: str, tgt: str, email: Optional[str]) -> Optional[str]:
    params = {"q": text, "langpair": f"{_MM[src]}|{_MM[tgt]}"}
    if email:
        params["de"] = email
    resp = await client.get(_ENDPOINT, params=params)
    resp.raise_for_status()
    data = resp.json()
    if str(data.get("responseStatus")) != "200":
        return None
    out = (data.get("responseData") or {}).get("translatedText")
    if not isinstance(out, str) or not out.strip():
        return None
    # MyMemory returns its rate-limit notice in this field with status 200 sometimes
    if "MYMEMORY WARNING" in out.upper():
        return None
    return out.strip()


async def translate_to_all(text: str, source: str) -> Dict[str, str]:
    """Return {lang_code: text} for every UI language. The source stays verbatim."""
    text = (text or "").strip()
    if not text:
        return {}
    if source not in LANGUAGES:
        source = "en"
    targets: List[str] = [c for c in LANGUAGES if c != source]
    email = settings.mymemory_email or None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            results = await asyncio.gather(*[_one(client, text, source, t, email) for t in targets])
    except (httpx.HTTPError, ValueError) as e:  # ValueError covers a malformed JSON body
        raise TranslationError(str(e)) from e

    out = {source: text}
    for tgt, value in zip(targets, results, strict=True):
        if value:
            out[tgt] = value
    if len(out) == 1:
        raise TranslationError("No translations returned (daily limit reached?)")
    return out
