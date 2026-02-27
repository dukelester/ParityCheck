# Authentication

ParityCheck uses JWT for web sessions and API keys for CLI access.

## Flow

1. **Register** → User signs up, receives verification email
2. **Verify** → User clicks link in email to verify
3. **Login** → User signs in, receives access + refresh tokens
4. **API Key** → Logged-in user creates API key for CLI

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register (sends verification email) |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| POST | `/api/v1/auth/verify-email` | Verify email with token |
| POST | `/api/v1/auth/resend-verification` | Resend verification email |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user (Bearer) |
| POST | `/api/v1/auth/api-keys` | Create API key (Bearer) |

## Email Verification

- Verification link: `{FRONTEND_URL}/verify-email?token={token}`
- Token expires in 24 hours (configurable)
- Login is blocked until email is verified

## Development

Set `DEV_SKIP_EMAIL=true` in `.env` to log verification links to the console instead of sending email.

For local SMTP testing, use [Mailpit](https://github.com/axllent/mailpit) or:

```bash
python -m smtpd -c DebuggingServer -n localhost:1025
```

## Environment Variables

See `backend/.env.example` for SMTP and auth configuration.
