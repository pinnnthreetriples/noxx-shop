"""Localized bot-facing strings for the 9 mini-app UI languages.

Mirrors apps/miniapp/src/app/i18n.ts; `mo` (Moldovan) copies `ro` (Romanian).
Two keys per language: `view` (inline button label) and `new_product`
(message template, formatted with the product `{title}`).
"""

_STRINGS = {
    "en": {"view": "View", "new_product": "🎬 New: {title}"},
    "ru": {"view": "Посмотреть", "new_product": "🎬 Новинка: {title}"},
    "de": {"view": "Ansehen", "new_product": "🎬 Neu: {title}"},
    "el": {"view": "Δείτε", "new_product": "🎬 Νέο: {title}"},
    "ro": {"view": "Vezi", "new_product": "🎬 Nou: {title}"},
    "bg": {"view": "Виж", "new_product": "🎬 Ново: {title}"},
    "sr": {"view": "Погледај", "new_product": "🎬 Ново: {title}"},
    "tr": {"view": "Görüntüle", "new_product": "🎬 Yeni: {title}"},
}
_STRINGS["mo"] = _STRINGS["ro"]


def t(lang: str, key: str) -> str:
    """Return the string for `lang`/`key`, falling back to English."""
    return _STRINGS.get(lang, _STRINGS["en"]).get(key, _STRINGS["en"][key])
