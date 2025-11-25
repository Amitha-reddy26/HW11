# app/models/user.py
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserResponse, Token

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)

    # 🔥 TESTS REQUIRE THIS:
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(name={self.first_name} {self.last_name}, email={self.email})>"

    # ----------------------------
    # PASSWORD METHODS (TESTED)
    # ----------------------------
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify password using stored password_hash"""
        return pwd_context.verify(plain_password, self.password_hash)

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, raw_password: str):
        # bcrypt cannot handle >72 byte passwords
        raw_password = raw_password[:72]
        self.password_hash = pwd_context.hash(raw_password)

    # ----------------------------
    # TOKEN LOGIC
    # ----------------------------
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[uuid.UUID]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            return uuid.UUID(user_id) if user_id else None
        except (JWTError, ValueError):
            return None

    # ----------------------------
    # REGISTRATION
    # ----------------------------
    @classmethod
    def register(cls, db, user_data: Dict[str, Any]) -> "User":
        try:
            # Pydantic validation first
            user_create = UserCreate.model_validate(user_data)

            new_user = cls(
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                username=user_create.username,
            )
            new_user.password = user_create.password  # Calls setter → hashes

            db.add(new_user)
            db.flush()
            return new_user

        except ValidationError as e:
            raise ValueError(str(e))

    # ----------------------------
    # AUTHENTICATION
    # ----------------------------
    @classmethod
    def authenticate(cls, db, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = db.query(cls).filter(
            (cls.username == username) | (cls.email == username)
        ).first()

        if not user or not user.verify_password(password):
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        user_response = UserResponse.model_validate(user)
        token_response = Token(
            access_token=cls.create_access_token({"sub": str(user.id)}),
            token_type="bearer",
            user=user_response
        )

        return token_response.model_dump()
