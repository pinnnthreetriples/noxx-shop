"""Admin content auto-translation via Gemini (Google AI).

The owner writes a title/description in one language; this fills the rest.
The API key stays server-side (settings.gemini_api_key) — never in the client.
"""
import json
from typing import Dict

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


class TranslationError(RuntimeError):
    """Auto-translation could not be produced (no key, upstream error, bad output)."""


async def translate_to_all(text: str, source: str) -> Dict[str, str]:
    """Return {lang_code: text} for every UI language. The source stays verbatim."""
    text = (text or "").strip()
    if not text:
        return {}
    if source not in LANGUAGES:
        source = "en"
    if not settings.gemini_api_key:
        raise TranslationError("Gemini API key is not configured")

    targets = {c: n for c, n in LANGUAGES.items() if c != source}
    prompt = (
        "You translate short e-commerce catalog labels and descriptions. "
        f"The text below is in {LANGUAGES[source]}. Translate it into each of these "
        "languages, keeping it natural and concise (a store category/product label or "
        "its description). Return ONLY a JSON object mapping the language code to the "
        "translation — no commentary.\n"
        f"Language codes: {json.dumps(targets, ensure_ascii=False)}\n"
        f"Text: {text}"
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
                },
            )
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw)
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise TranslationError(str(e)) from e

    result = {source: text}
    for code in LANGUAGES:
        value = parsed.get(code)
        if code != source and isinstance(value, str) and value.strip():
            result[code] = value.strip()
    return result
