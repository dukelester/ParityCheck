"""Authentication service."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ApiKey, User
from app.services.email import send_password_reset_email, send_verification_email


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit; encode and truncate if needed
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


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
    # Return naive UTC for TIMESTAMP WITHOUT TIME ZONE columns (asyncpg compatibility)
    return (datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)).replace(tzinfo=None)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def password_reset_token_expires_at() -> datetime:
    return (
        datetime.now(timezone.utc)
        + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
    ).replace(tzinfo=None)


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
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(User).where(
            User.verification_token == token,
            User.verification_token_expires > now_utc,
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
        .where(ApiKey.key == key, (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)))
    )
    return result.scalar_one_or_none()


async def get_user_and_workspace_by_api_key(
    db: AsyncSession, key: str
) -> tuple[User | None, UUID | None]:
    """Return (user, workspace_id). workspace_id may be None for legacy keys."""
    result = await db.execute(
        select(User, ApiKey.workspace_id)
        .join(ApiKey, ApiKey.user_id == User.id)
        .where(ApiKey.key == key, (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)))
    )
    row = result.one_or_none()
    if not row:
        return None, None
    return row[0], row[1]


async def create_api_key(
    db: AsyncSession, user_id: UUID, workspace_id: UUID | None = None
) -> str:
    key = generate_api_key()
    api_key = ApiKey(user_id=user_id, workspace_id=workspace_id, key=key)
    db.add(api_key)
    return key


async def get_user_by_password_reset_token(
    db: AsyncSession, token: str
) -> User | None:
    """Find user by valid password reset token."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(User).where(
            User.password_reset_token == token,
            User.password_reset_token_expires > now_utc,
        )
    )
    return result.scalar_one_or_none()


async def reset_user_password(
    db: AsyncSession, user: User, new_password: str
) -> None:
    """Update user password and clear reset token."""
    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
