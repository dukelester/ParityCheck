"""GitHub OAuth service."""

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import User
from app.services.auth import create_access_token, create_refresh_token


GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


def get_github_auth_url(state: str) -> str:
    """Build GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.BACKEND_URL.rstrip('/')}{settings.GITHUB_CALLBACK_PATH}",
        "scope": "user:email",
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> str | None:
    """Exchange authorization code for GitHub access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("access_token")


async def fetch_github_user(access_token: str) -> dict | None:
    """Fetch GitHub user profile."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
    if resp.status_code != 200:
        return None
    return resp.json()


async def fetch_github_primary_email(access_token: str) -> str | None:
    """Fetch primary email from GitHub (needed if user has private email)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GITHUB_EMAILS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
    if resp.status_code != 200:
        return None
    emails = resp.json()
    for e in emails:
        if e.get("primary"):
            return e.get("email")
    return emails[0].get("email") if emails else None


async def get_or_create_github_user(
    db: AsyncSession,
    github_id: str,
    email: str,
    name: str,
) -> User:
    """Get existing user by github_id or email, or create new one."""
    # Try by github_id first
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    if user:
        # Update name/email if changed
        if user.name != name or user.email != email.lower():
            user.name = name
            user.email = email.lower()
        return user

    # Try by email (link existing account)
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user:
        user.github_id = github_id
        user.email_verified = True  # GitHub email is verified
        return user

    # Create new user
    user = User(
        email=email.lower(),
        name=name,
        hashed_password=None,
        github_id=github_id,
        email_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def generate_oauth_state() -> str:
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_oauth_state(state: str) -> bool:
    try:
        jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return True
    except JWTError:
        return False
