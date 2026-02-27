"""Authentication service."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ApiKey, User
from app.services.email import send_verification_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def verification_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)


def generate_api_key() -> str:
    return f"pc_{secrets.token_urlsafe(32)}"


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str,
) -> tuple[User, str]:
    """Create user and return (user, verification_token)."""
    hashed = hash_password(password)
    token = generate_verification_token()
    expires = verification_token_expires_at()

    user = User(
        email=email.lower(),
        hashed_password=hashed,
        name=name,
        email_verified=False,
        verification_token=token,
        verification_token_expires=expires,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await send_verification_email(user.email, token, user.name)
    return user, token


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def verify_email_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(
        select(User).where(
            User.verification_token == token,
            User.verification_token_expires > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()
    if user:
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
    return user


async def get_user_by_api_key(db: AsyncSession, key: str) -> User | None:
    result = await db.execute(
        select(User)
        .join(ApiKey, ApiKey.user_id == User.id)
        .where(ApiKey.key == key, (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > datetime.now(timezone.utc)))
    )
    return result.scalar_one_or_none()


async def create_api_key(db: AsyncSession, user_id: UUID) -> str:
    key = generate_api_key()
    api_key = ApiKey(user_id=user_id, key=key)
    db.add(api_key)
    return key
