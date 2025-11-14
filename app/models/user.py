from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from app.db.base import Base

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserResponse, Token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        self.password_hash = value

    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"<User(name={full_name}, email={self.email})>"



    @staticmethod
    def hash_password(password: str) -> str:
        password = password[:72]
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, self.password_hash)



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


    @classmethod
    def register(cls, db, user_data: Dict[str, Any]):
        password = user_data.get("password", "")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        existing_user = db.query(cls).filter(
            (cls.email == user_data.get("email")) |
            (cls.username == user_data.get("username"))
        ).first()

        if existing_user:
            raise ValueError("Username or email already exists")

        try:
            user_create = UserCreate.model_validate(user_data)
        except ValidationError as e:
            raise ValueError(str(e))

        new_user = cls(
            username=user_create.username,
            email=user_create.email,
            password_hash=cls.hash_password(user_create.password),
            first_name=user_create.first_name,
            last_name=user_create.last_name,
        )

        db.add(new_user)
        db.flush()
        return new_user
 
    @classmethod
    def authenticate(cls, db, username: str, password: str):
        user = db.query(cls).filter(
            (cls.username == username) | (cls.email == username)
        ).first()

        if not user or not user.verify_password(password):
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        user_response = UserResponse.model_validate(user)

        token_resp = Token(
            access_token=cls.create_access_token({"sub": str(user.id)}),
            token_type="bearer",
            user=user_response
        )

        return token_resp.model_dump()
