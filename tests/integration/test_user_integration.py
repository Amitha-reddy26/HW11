import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.database_init import init_db
from app.models.user import User


@pytest.fixture(scope="module")
def db():
    # Initialize tables in the test database
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_register_user_success(db: Session):
    user_data = {
        "username": "integration_user",
        "email": "integration@example.com",
        "password": "StrongPass123",
        "first_name": "Test",
        "last_name": "User"
    }

    user = User.register(db, user_data)
    db.commit()

    assert user.id is not None
    assert user.username == "integration_user"
    assert user.email == "integration@example.com"
    assert user.password_hash != user_data["password"]  # Password is hashed


def test_unique_email_constraint(db: Session):
    first = {
        "username": "user_email_1",
        "email": "duplicate_email@example.com",
        "password": "StrongPass123",
    }
    second = {
        "username": "user_email_2",
        "email": "duplicate_email@example.com",  # same email
        "password": "StrongPass123",
    }

    User.register(db, first)
    db.commit()

    with pytest.raises(ValueError):
        User.register(db, second)


def test_unique_username_constraint(db: Session):
    first = {
        "username": "duplicate_username",
        "email": "first_username@example.com",
        "password": "StrongPass123",
    }
    second = {
        "username": "duplicate_username",  # same username
        "email": "second_username@example.com",
        "password": "StrongPass123",
    }

    User.register(db, first)
    db.commit()

    with pytest.raises(ValueError):
        User.register(db, second)


def test_authenticate_success(db: Session):
    user_data = {
        "username": "login_test_user",
        "email": "login_test@example.com",
        "password": "StrongPass123",
    }

    User.register(db, user_data)
    db.commit()

    token_response = User.authenticate(db, "login_test_user", "StrongPass123")

    assert token_response is not None
    assert "access_token" in token_response
    assert token_response["token_type"] == "bearer"
    assert token_response["user"]["username"] == "login_test_user"


def test_authenticate_invalid_password(db: Session):
    user_data = {
        "username": "login_fail_user",
        "email": "login_fail@example.com",
        "password": "CorrectPass123",
    }

    User.register(db, user_data)
    db.commit()

    result = User.authenticate(db, "login_fail_user", "WrongPassword")

    assert result is None
