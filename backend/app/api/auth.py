"""Authentication endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import (
    ApiKeyResponse,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import (
    create_access_token,
    create_api_key,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_api_key,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    verify_email_token,
    verify_password,
)
from app.services.email import send_verification_email

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserResponse)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user. Sends verification email."""
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user, _ = await create_user(db, payload.email, payload.password, payload.name)
    await db.commit()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        created_at=user.created_at.isoformat(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password. Returns JWT tokens."""
    user = await get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for the verification link.",
        )

    access = create_access_token(str(user.id), user.email)
    refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify email with token from verification link."""
    user = await verify_email_token(db, payload.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email."""
    user = await get_user_by_email(db, payload.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link was sent"}

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    from app.services.auth import generate_verification_token, verification_token_expires_at

    user.verification_token = generate_verification_token()
    user.verification_token_expires = verification_token_expires_at()
    await db.flush()
    await send_verification_email(user.email, user.verification_token, user.name)
    await db.commit()

    return {"message": "If the email exists, a verification link was sent"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    token = payload.refresh_token
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token required")

    decoded = decode_token(token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = decoded.get("sub")
    user = await get_user_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access = create_access_token(str(user.id), user.email)
    refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """Get current user. Requires Bearer token."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    decoded = decode_token(credentials.credentials)
    if not decoded or decoded.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = decoded.get("sub")
    user = await get_user_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        created_at=user.created_at.isoformat(),
    )


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_user_api_key(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """Create a new API key for CLI usage. Requires Bearer token."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    decoded = decode_token(credentials.credentials)
    if not decoded or decoded.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = UUID(decoded["sub"])
    key = await create_api_key(db, user_id)
    await db.commit()

    return ApiKeyResponse(api_key=key)


# --- Dependencies for protected routes ---


async def get_current_user(
    db: AsyncSession,
    api_key: str | None,
    credentials: HTTPAuthorizationCredentials | None,
) -> User | None:
    """Resolve user from API key or Bearer token."""
    if api_key:
        return await get_user_by_api_key(db, api_key)
    if credentials:
        decoded = decode_token(credentials.credentials)
        if decoded and decoded.get("type") == "access":
            user = await get_user_by_id(db, UUID(decoded["sub"]))
            return user
    return None


async def get_current_user_id(
    api_key: str | None = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Validate API key or Bearer token; return user_id. For use in Depends()."""
    user = await get_current_user(db, api_key, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key or Bearer token required",
        )
    return str(user.id)
