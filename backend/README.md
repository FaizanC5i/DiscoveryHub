# Discovery Hub Backend

FastAPI service with Azure SQL, JWT access tokens, rotating refresh tokens and password reset.

## Requirements

- Python 3.11 or newer (the team uses 3.14)
- ODBC Driver 18 for SQL Server installed on the machine
- Network access to the Azure SQL server (the server firewall must allow your IP)

## Setup

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env      # then edit .env with real values
```

Generate a JWT secret and put it in `.env` as `JWT_SECRET_KEY`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

The server refuses to start if the secret is shorter than 32 characters or is a placeholder.

## Database migrations

Tables are created by Alembic, never by hand:

```powershell
alembic upgrade head        # apply 001, 002, 003
alembic downgrade -1        # undo the most recent migration
```

Migrations, in order:

| Revision | Creates |
|---|---|
| `001_create_users` | `users` |
| `002_create_refresh_tokens` | `refresh_tokens` |
| `003_create_password_reset_tokens` | `password_reset_tokens` |

Verify the schema and foreign keys work against the live database:

```powershell
python scripts/verify_db.py
```

## Run the server

```powershell
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

## Endpoints

All auth endpoints live under `/api/auth`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/signup` | Create an account and sign in (201) |
| POST | `/login` | Sign in. 404 `ACCOUNT_NOT_FOUND` if no account exists |
| POST | `/logout` | End this session and clear cookies |
| POST | `/refresh` | Rotate the refresh token and issue a new access token |
| POST | `/forgot-password` | Send a reset link (always the same response) |
| POST | `/reset-password` | Set a new password with a one-time token |
| GET | `/me` | Return the signed-in user (401 if not signed in) |

Errors use one shape: `{"detail": {"code": "...", "message": "..."}}`.

## Layout

```
app/
  main.py              app factory: CORS, rate limiting, routers
  core/                config, security, cookies, time, rate limit
  db/                  engine/session, ORM models
  api/routes/auth.py   HTTP endpoints
  schemas/auth.py      request and response models
  dependencies/auth.py get_current_user
  services/            auth rules and email sending
alembic/               migrations (versions/001..003)
scripts/verify_db.py   live database check
```

## Security notes

- Passwords are hashed with Argon2id. Raw passwords and tokens are never stored or logged.
- Refresh and reset tokens are random, and only their SHA-256 hashes are stored.
- Access tokens are HS256 JWTs with a 15-minute lifetime. The algorithm is pinned on verification.
- Cookies are HttpOnly and SameSite=Lax. Set `COOKIE_SECURE=true` (or `ENVIRONMENT=production`) behind HTTPS.
- Reuse of a rotated refresh token outside a 10-second grace window revokes every session for that user.
- Password reset revokes every session for the user.
