import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.user import UserCreate



def test_usercreate_valid_data():
    data = {
        "username": "john123",
        "email": "john@example.com",
        "password": "StrongPass123",
    }

    user = UserCreate(**data)

    assert user.username == "john123"
    assert user.email == "john@example.com"
    assert user.password == "StrongPass123"


def test_usercreate_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            username="bademail",
            email="not-an-email",
            password="StrongPass123"
        )


def test_usercreate_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            username="shortpass",
            email="test@example.com",
            password="123"  # too short
        )
