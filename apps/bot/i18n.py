"""Localized bot-facing strings for the 9 mini-app UI languages.

Mirrors apps/miniapp/src/app/i18n.ts; `mo` (Moldovan) copies `ro` (Romanian).
`view`/`open_*` are inline button labels, `new_product` is a template
(formatted with the product `{title}`), the `*_cmd` keys answer bot commands.
"""

_STRINGS = {
    "en": {
        "view": "View", "new_product": "🎬 New: {title}",
        "welcome": "Welcome! Open the mini app to browse the video catalog.",
        "open_app": "Open shop",
        "support_cmd": "Support is available in the mini app: Profile → Support.",
        "paysupport_cmd": "For payment issues, create a support ticket with the topic “Payment issue”.",
        "terms_cmd": "Terms of use and the refund policy are available in the mini app.",
        "open_support": "Contact support",
        "open_terms": "Open terms",
    },
    "ru": {
        "view": "Посмотреть", "new_product": "🎬 Новинка: {title}",
        "welcome": "Добро пожаловать! Открывай мини-апп и смотри каталог видео.",
        "open_app": "Открыть магазин",
        "support_cmd": "Поддержка доступна в мини-аппе: Профиль → Поддержка.",
        "paysupport_cmd": "По вопросам оплаты создай тикет в поддержке с темой «Проблема с оплатой».",
        "terms_cmd": "Условия использования и политика возврата — в мини-аппе.",
        "open_support": "Написать в поддержку",
        "open_terms": "Открыть условия",
    },
    "de": {
        "view": "Ansehen", "new_product": "🎬 Neu: {title}",
        "welcome": "Willkommen! Öffne die Mini-App und stöbere im Videokatalog.",
        "open_app": "Shop öffnen",
        "support_cmd": "Der Support ist in der Mini-App verfügbar: Profil → Support.",
        "paysupport_cmd": "Bei Zahlungsproblemen erstelle ein Support-Ticket mit dem Thema „Zahlungsproblem“.",
        "terms_cmd": "Die Nutzungsbedingungen und die Rückerstattungsrichtlinie findest du in der Mini-App.",
        "open_support": "Support kontaktieren",
        "open_terms": "Bedingungen öffnen",
    },
    "el": {
        "view": "Δείτε", "new_product": "🎬 Νέο: {title}",
        "welcome": "Καλώς ήρθες! Άνοιξε το mini app για να δεις τον κατάλογο βίντεο.",
        "open_app": "Άνοιγμα καταστήματος",
        "support_cmd": "Η υποστήριξη είναι διαθέσιμη στο mini app: Προφίλ → Υποστήριξη.",
        "paysupport_cmd": "Για προβλήματα πληρωμής, δημιούργησε αίτημα υποστήριξης με θέμα «Πρόβλημα πληρωμής».",
        "terms_cmd": "Οι όροι χρήσης και η πολιτική επιστροφών βρίσκονται στο mini app.",
        "open_support": "Επικοινωνία με υποστήριξη",
        "open_terms": "Άνοιγμα όρων",
    },
    "ro": {
        "view": "Vezi", "new_product": "🎬 Nou: {title}",
        "welcome": "Bine ai venit! Deschide mini-aplicația și răsfoiește catalogul video.",
        "open_app": "Deschide magazinul",
        "support_cmd": "Suportul este disponibil în mini-aplicație: Profil → Suport.",
        "paysupport_cmd": "Pentru probleme de plată, creează un tichet de suport cu subiectul „Problemă de plată”.",
        "terms_cmd": "Termenii de utilizare și politica de rambursare sunt în mini-aplicație.",
        "open_support": "Contactează suportul",
        "open_terms": "Deschide termenii",
    },
    "bg": {
        "view": "Виж", "new_product": "🎬 Ново: {title}",
        "welcome": "Добре дошъл! Отвори мини приложението и разгледай видео каталога.",
        "open_app": "Отвори магазина",
        "support_cmd": "Поддръжката е налична в мини приложението: Профил → Поддръжка.",
        "paysupport_cmd": "При проблеми с плащането създай тикет с тема „Проблем с плащане“.",
        "terms_cmd": "Условията за ползване и политиката за възстановяване са в мини приложението.",
        "open_support": "Пиши на поддръжката",
        "open_terms": "Отвори условията",
    },
    "sr": {
        "view": "Погледај", "new_product": "🎬 Ново: {title}",
        "welcome": "Добродошли! Отвори мини-апликацију и погледај видео каталог.",
        "open_app": "Отвори продавницу",
        "support_cmd": "Подршка је доступна у мини-апликацији: Профил → Подршка.",
        "paysupport_cmd": "За проблеме са плаћањем направи тикет са темом „Проблем са плаћањем“.",
        "terms_cmd": "Услови коришћења и политика повраћаја су у мини-апликацији.",
        "open_support": "Контактирај подршку",
        "open_terms": "Отвори услове",
    },
    "tr": {
        "view": "Görüntüle", "new_product": "🎬 Yeni: {title}",
        "welcome": "Hoş geldin! Mini uygulamayı aç ve video kataloğuna göz at.",
        "open_app": "Mağazayı aç",
        "support_cmd": "Destek mini uygulamada: Profil → Destek.",
        "paysupport_cmd": "Ödeme sorunları için «Ödeme sorunu» konulu bir destek talebi oluştur.",
        "terms_cmd": "Kullanım koşulları ve iade politikası mini uygulamada.",
        "open_support": "Desteğe yaz",
        "open_terms": "Koşulları aç",
    },
}
_STRINGS["mo"] = _STRINGS["ro"]


def t(lang: str, key: str) -> str:
    """Return the string for `lang`/`key`, falling back to English."""
    return _STRINGS.get(lang, _STRINGS["en"]).get(key, _STRINGS["en"][key])


def norm_lang(code: str | None) -> str:
    """Map a Telegram client language_code (e.g. 'ru-RU') to a supported UI
    language, falling back to English. Used where the DB choice is unknown."""
    base = (code or "").lower().split("-")[0]
    return base if base in _STRINGS else "en"


def green_btn(label: str) -> str:
    """Telegram can't color inline buttons, so every bot button carries a
    green dot as the house style. Prefix here, at the single choke point."""
    return f"🟢 {label}"
