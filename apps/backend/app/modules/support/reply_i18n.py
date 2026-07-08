"""Localized bot-nudge strings for the 9 mini-app UI languages.

Kept self-contained (no bot i18n import — separate app); `mo` (Moldovan)
copies `ro` (Romanian). `nudge` is the bell notice, `open` the button label.
"""

_STRINGS = {
    "en": {"nudge": "Reply from support", "open": "Open"},
    "ru": {"nudge": "Ответ от поддержки", "open": "Открыть"},
    "de": {"nudge": "Antwort vom Support", "open": "Öffnen"},
    "el": {"nudge": "Απάντηση από την υποστήριξη", "open": "Άνοιγμα"},
    "ro": {"nudge": "Răspuns de la suport", "open": "Deschide"},
    "bg": {"nudge": "Отговор от поддръжката", "open": "Отвори"},
    "sr": {"nudge": "Одговор подршке", "open": "Отвори"},
    "tr": {"nudge": "Destekten yanıt", "open": "Aç"},
}
_STRINGS["mo"] = _STRINGS["ro"]


def nudge_text(lang: str) -> str:
    """Bell-notice text for `lang`, falling back to English."""
    return _STRINGS.get(lang, _STRINGS["en"])["nudge"]


def open_label(lang: str) -> str:
    """Button label for `lang`, falling back to English."""
    return _STRINGS.get(lang, _STRINGS["en"])["open"]
