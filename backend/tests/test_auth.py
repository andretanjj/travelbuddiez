from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.services import auth_service


def test_password_hash_is_not_plain_password():
    # pytest style: arrange input, call the function, then assert expected output.
    # This checks that we do not store the user's raw password directly.
    plain_password = "mypassword123"
    hashed_password = auth_service.get_password_hash(plain_password)
    assert hashed_password != plain_password


def test_verify_password_with_correct_password():
    # The same password used to create the hash should pass verification.
    plain_password = "mypassword123"
    hashed_password = auth_service.get_password_hash(plain_password)
    result = auth_service.verify_password(plain_password, hashed_password)
    assert result is True


def test_verify_password_with_wrong_password():
    # A different password should NOT match the stored password hash.
    plain_password = "mypassword123"
    wrong_password = "wrongpassword"
    hashed_password = auth_service.get_password_hash(plain_password)
    result = auth_service.verify_password(wrong_password, hashed_password)
    assert result is False


def test_create_access_token_success(monkeypatch):
    # Replace JWT secret during test so we do not depend on the real .env file.
    monkeypatch.setattr(auth_service, "JWT_SECRET_KEY", "test-secret-key")

    token = auth_service.create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(minutes=30),
    )

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_missing_secret(monkeypatch):
    # pytest.raises checks that the function fails correctly when config is missing.
    monkeypatch.setattr(auth_service, "JWT_SECRET_KEY", None)

    with pytest.raises(ValueError):
        auth_service.create_access_token(data={"sub": "testuser"})