from app.core.security import hash_password, verify_password, create_admin_token, decode_admin_token


def test_password_hash():
    h = hash_password("secret")
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)


def test_admin_token_roundtrip():
    token = create_admin_token(42)
    payload = decode_admin_token(token)
    assert payload["sub"] == "42"
