from app.modules.catalog.service import resolve_language
from app.modules.users.models import User


def test_resolve_language_from_user():
    user = User(language_code="ru", selected_language=None)
    assert resolve_language(user) == "ru"


def test_resolve_language_selected():
    user = User(language_code="fr", selected_language="de")
    assert resolve_language(user) == "de"


def test_resolve_language_unsupported():
    user = User(language_code="xx", selected_language=None)
    assert resolve_language(user) == "en"
