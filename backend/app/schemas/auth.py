"""Auth schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    email_verified: bool
    created_at: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ApiKeyResponse(BaseModel):
    api_key: str
    message: str = "Store this key securely. It won't be shown again."


class UpdateProfileRequest(BaseModel):
    """Update basic profile fields."""

    name: str = Field(..., min_length=1, max_length=255)


class ChangeEmailRequest(BaseModel):
    """Request email change for current user."""

    new_email: EmailStr
    current_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password for current user."""

    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    """Delete current user account."""

    current_password: str = Field(..., min_length=8, max_length=128)
    confirm: str = Field(..., min_length=1, description="Must be 'delete my account'")
