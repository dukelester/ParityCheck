"""Authentication endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import iso_utc
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import (
    ApiKeyResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
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
    generate_password_reset_token,
    get_user_and_workspace_by_api_key,
    get_user_by_api_key,
    get_user_by_email,
    get_user_by_id,
    get_user_by_password_reset_token,
    hash_password,
    password_reset_token_expires_at,
    reset_user_password,
    verify_email_token,
    verify_password,
)
from app.services.email import send_password_reset_email, send_verification_email
from app.services.github_oauth import (
    exchange_code_for_token,
    fetch_github_primary_email,
    fetch_github_user,
    generate_oauth_state,
    get_github_auth_url,
    get_or_create_github_user,
    verify_oauth_state,
)

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer = HTTPBearer(auto_error=False)


def _extract_api_key_from_request(
    api_key: str | None,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Get API key from X-API-Key header or Authorization: Bearer/ApiKey."""
    if api_key:
        return api_key
    if credentials:
        # ApiKey scheme: Authorization: ApiKey pc_xxx
        if credentials.scheme.lower() == "apikey":
            return credentials.credentials
        # Bearer with API key (CLI sends Bearer + api_key): treat as API key if it looks like one
        if credentials.scheme.lower() == "bearer" and credentials.credentials.startswith("pc_"):
            return credentials.credentials
    return None


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

    try:
        user, _ = await create_user(db, payload.email, payload.password, payload.name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Registration failed: %s", e)
        detail = "Registration failed. Please try again."
        if "smtp" in str(e).lower() or "email" in str(e).lower() or "auth" in str(e).lower():
            detail = "Could not send verification email. Check SMTP settings (Gmail: use App Password, enable 2FA)."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        created_at=iso_utc(user.created_at),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password. Returns JWT tokens."""
    user = await get_user_by_email(db, payload.email)
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
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

    from app.services.auth import (
    generate_verification_token,
    verification_token_expires_at,
)

    user.verification_token = generate_verification_token()
    user.verification_token_expires = verification_token_expires_at()
    await db.flush()
    try:
        await send_verification_email(user.email, user.verification_token, user.name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Resend verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send email. Check SMTP configuration.",
        ) from e
    await db.commit()

    return {"message": "If the email exists, a verification link was sent"}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset. Sends email with reset link."""
    user = await get_user_by_email(db, payload.email)
    if not user:
        return {"message": "If the email exists, a reset link was sent"}

    if not user.hashed_password:
        return {"message": "If the email exists, a reset link was sent"}

    user.password_reset_token = generate_password_reset_token()
    user.password_reset_token_expires = password_reset_token_expires_at()
    await db.flush()
    try:
        await send_password_reset_email(
            user.email, user.password_reset_token, user.name
        )
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception("Password reset email failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send email. Check SMTP configuration.",
        ) from e
    await db.commit()

    return {"message": "If the email exists, a reset link was sent"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token from email link."""
    user = await get_user_by_password_reset_token(db, payload.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    await reset_user_password(db, user, payload.new_password)
    await db.commit()

    return {"message": "Password reset successfully"}


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub login is not configured",
        )
    state = generate_oauth_state()
    url = get_github_auth_url(state)
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback. Redirects to frontend with tokens in fragment."""
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_denied",
            status_code=302,
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_invalid",
            status_code=302,
        )

    if not verify_oauth_state(state):
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_denied",
            status_code=302,
        )

    token = await exchange_code_for_token(code)
    if not token:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed",
            status_code=302,
        )

    gh_user = await fetch_github_user(token)
    if not gh_user:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed",
            status_code=302,
        )

    email = gh_user.get("email")
    if not email:
        email = await fetch_github_primary_email(token)
    if not email:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_no_email",
            status_code=302,
        )

    github_id = str(gh_user["id"])
    name = gh_user.get("name") or gh_user.get("login") or "User"

    user = await get_or_create_github_user(db, github_id, email, name)
    await db.commit()

    access = create_access_token(str(user.id), user.email)
    refresh = create_refresh_token(str(user.id))

    # Redirect to frontend with tokens in fragment (not sent to server)
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback#access_token={access}&refresh_token={refresh}&expires_in={settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60}"
    return RedirectResponse(url=redirect_url, status_code=302)


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
        created_at=iso_utc(user.created_at),
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
    from app.services.workspace import get_or_create_default_workspace

    ws = await get_or_create_default_workspace(db, user_id)
    key = await create_api_key(db, user_id, ws.id)
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
    effective_key = _extract_api_key_from_request(api_key, credentials)
    user = await get_current_user(db, effective_key, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key or Bearer token required",
        )
    return str(user.id)


async def get_current_user_and_workspace(
    api_key: str | None = Depends(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, UUID | None]:
    """Return (user_id, workspace_id). workspace_id is None for Bearer auth."""
    effective_key = _extract_api_key_from_request(api_key, credentials)
    if effective_key:
        user, ws_id = await get_user_and_workspace_by_api_key(db, effective_key)
        if user:
            return str(user.id), ws_id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    if credentials and credentials.scheme.lower() == "bearer":
        decoded = decode_token(credentials.credentials)
        if decoded and decoded.get("type") == "access":
            user = await get_user_by_id(db, UUID(decoded["sub"]))
            if user:
                return str(user.id), None
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key or Bearer token required",
    )
