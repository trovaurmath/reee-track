import uuid

from app.modules.identity.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hash_does_not_store_plain_text() -> None:
    plain_text = "a-long-test-password"

    hashed = hash_password(plain_text)

    assert hashed != plain_text
    assert verify_password(plain_text, hashed)
    assert not verify_password("another-password", hashed)


def test_access_and_refresh_tokens_have_expected_identity() -> None:
    user_id = uuid.uuid4()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token()

    assert decode_access_token(access_token) == user_id
    assert hash_refresh_token(refresh_token.raw_token) == refresh_token.token_hash

