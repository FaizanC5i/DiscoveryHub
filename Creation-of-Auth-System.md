# Creation of the Auth System

This document records how the Discovery Hub authentication system was designed and built: the technologies, why each was chosen, every file created or changed, how data moves through the system, the problems hit along the way, and how it was tested. Read it top to bottom to explain the system, or jump to a section when someone asks a specific question.

---

## 1. What was built

A complete, database-backed authentication feature:

- **Sign up**: create an account and sign in immediately.
- **Login**: check email and password, start a session.
- **Logout**: end the session on the server and clear the browser cookies.
- **Token refresh**: silently renew an expired access token using a long-lived refresh token, with rotation and reuse detection.
- **Forgot password**: send a one-time reset link (generic response, so emails cannot be probed).
- **Reset password**: set a new password with that link, then end all sessions.
- **Dashboard protection**: pages under the signed-in area are only served to a valid session.

Storage is Azure SQL. Sessions live in HttpOnly cookies. Passwords and tokens are never stored in plain text.

---

## 2. Technologies used and why

### Backend (Python)

| Technology | Version | What it does here | Why it was chosen |
|---|---|---|---|
| **Python** | 3.14.6 (installed locally) | Runtime for the backend | Already the team's version (README says 3.14). Libraries require 3.10 or 3.11+. |
| **FastAPI** | 0.162.0 | Web framework: routes, request validation, responses, dependency injection | Already in the project. Generates request validation from type hints and interactive docs at `/docs`. |
| **Uvicorn** | 0.54.0 | ASGI server that runs FastAPI | The standard server for FastAPI. `--reload` restarts on code changes during development. |
| **Starlette** | 1.10.0 | Underlying web toolkit used by FastAPI (CORS middleware, requests, responses) | Pulled in by FastAPI; pinned so the version is reproducible. |
| **Pydantic** | 2.14.3 | Validates and cleans request data (`SignUpRequest`, `LoginRequest`, etc.) | FastAPI's built-in validation layer. A bad request is rejected before any business code runs. |
| **pydantic-settings** | 2.16.2 | Reads configuration from environment variables and `.env` into a typed `Settings` object | Keeps secrets out of source code. Type checks run at startup, so a missing or malformed value fails immediately. |
| **SQLAlchemy** | 2.1.8 | ORM and SQL toolkit: models, sessions, queries, transactions | Industry-standard Python database layer. Lets models be Python classes instead of hand-written SQL strings. |
| **pyodbc** | 5.5.0 | ODBC driver bridge used by SQLAlchemy to talk to SQL Server | Azure SQL is reached through Microsoft's ODBC Driver 18. pyodbc is the Python binding for it. |
| **ODBC Driver 18 for SQL Server** | system install | The actual driver that speaks the SQL Server protocol with `Encrypt=yes` | Microsoft's current driver; required by Azure SQL's encryption defaults. Installed on the machine already. |
| **Alembic** | 1.20.1 | Database migrations: versioned, ordered, reversible schema changes | Creates and changes tables through numbered files so every environment ends up with the same schema. Replaces hand-run SQL. |
| **argon2-cffi** | 25.1.0 | Password hashing with Argon2id | Argon2id is the current recommended password hash. It is memory-hard, so guessing is slow. No 72-byte limit (bcrypt has one). |
| **PyJWT** | 2.15.1 | Creates and verifies JWT access tokens (HS256) | Small, standard JWT library. Signature checking and expiry checking are built in. |
| **slowapi** | 0.1.10 (uses `limits` 5.8.0) | Rate limiting per IP on login and forgot-password | FastAPI-friendly wrapper around the `limits` library. Stops password guessing and email flooding. |
| **email-validator** | 2.3.0 | Validates email format for `EmailStr` fields | Pydantic uses it to reject malformed emails with a clear message. |
| **dnspython**, **idna** | 2.9.2, 3.20 | Dependencies of email-validator (domain checks, international domains) | Pulled in automatically; pinned for reproducibility. |
| **Python standard library** | — | `secrets` (random tokens), `hashlib` (SHA-256), `smtplib`/`email` (sending mail), `logging`, `datetime`, `urllib` | Built-in, audited, no extra dependency. `secrets` is the correct source of randomness for security tokens. |

### Frontend (TypeScript / React)

| Technology | Version | What it does here | Why it was chosen |
|---|---|---|---|
| **Next.js** | 16.4.5 | App Router: pages, layouts, server components, proxy, server-side session check | Already in the project. Server components can read cookies and call the backend before HTML is sent. |
| **React** | 19.3.0 | UI components, forms, Suspense boundaries | Already in the project. Suspense is required for request-time reads under Cache Components. |
| **TypeScript** | 5.x | Type checking across the frontend | Catches wrong field names and wrong response shapes at build time. |
| **Tailwind CSS** | 4.x | Styling through design tokens (`bg-surface`, `text-fg`, etc.) | Project standard. Design system tokens keep colours and spacing consistent. |
| **server-only** | 0.0.1 | Makes the build fail if a client component imports server session code | Prevents accidental exposure of server-side auth logic to the browser. The package's only published version. |
| **Playwright (`playwright-core`)** | 1.64.1 | Browser automation used only for testing, in a scratch folder | Drives the real UI in Chromium to check flows end to end. |
| **ESLint** | 9.x | Linting | Project standard. |

### Infrastructure and services

| Service | Why |
|---|---|
| **Azure SQL Database** (`neuroxdatabase.database.windows.net`, database `Discoveryhub`) | Managed SQL Server, already provisioned for the project. Encrypted connections by default. |
| **Browser cookies** (HttpOnly, SameSite=Lax) | JavaScript cannot read them, which blocks token theft through injected scripts. The browser sends them automatically. |

---

## 3. Key concepts and why each one matters

**Password hashing (Argon2id).** Passwords are never stored. The system stores a salted, memory-hard hash. Checking a login means hashing the typed password with the same salt and comparing. Plain SHA-256 was rejected because it is too fast; a stolen table could be attacked at billions of guesses per second.

**Access token (JWT, 15 minutes).** A signed statement "user 42 is signed in until time X". The server checks the signature, so it does not need to ask the database every time. It is short-lived because it cannot be revoked instantly. The algorithm is pinned to HS256 so an attacker cannot send a token with `alg: none`.

**Refresh token (30 days, opaque).** A random 48-byte string. The browser keeps the raw value. The database keeps only its SHA-256 hash, so a database leak does not reveal usable sessions. It can be revoked at any time.

**Refresh rotation.** Every refresh cancels the old refresh token and issues a new one. A stolen token becomes useless the next time its owner refreshes.

**Reuse detection.** If a token that was already rotated comes back, either a thief replayed it or the legitimate client retried. The system cannot tell which, so it revokes every session for that user. A 10-second grace window handles the harmless case of two requests racing (for example two tabs refreshing at once).

**Reset token (30 minutes, single use).** Random, emailed as a link, stored as a hash with a `used_at` timestamp. Using it sets `used_at`, so it cannot be used twice. Requesting a new link cancels older unused links.

**Generic responses.** Forgot-password returns the same message whether or not the email exists, so it cannot be used to discover accounts. (Login deliberately does not do this; see section 12.)

**Rate limiting.** Login: 5 attempts per minute per IP. Forgot-password: 3 per minute. Beyond that the server returns 429.

**HttpOnly, SameSite=Lax, Secure cookies.** HttpOnly hides the cookie from JavaScript. SameSite=Lax stops most cross-site request forgery. Secure (on in production) means HTTPS only.

**Cookie scope (path "/").** Both cookies use path `/`, so the Next.js proxy and server pages receive them, not just the API.

**Dependency injection (FastAPI).** `get_db` gives each request its own database session and closes it afterward. `get_current_user` checks the access cookie and reloads the user, so a disabled user loses access immediately.

**Migrations (Alembic).** Each change to the schema is a numbered file with `upgrade` and `downgrade`. Applying `alembic upgrade head` brings any environment to the same state.

**Connection pooling with pre-ping.** SQLAlchemy keeps database connections open for reuse. `pool_pre_ping=True` tests a connection before using it, because Azure SQL closes idle connections.

**Settings validation.** The JWT secret must be at least 32 characters and not a placeholder, or the server refuses to start.

**Error shape.** Every auth error uses the same JSON: `{"detail": {"code": "...", "message": "..."}}`. The frontend branches on `code`, never on message text.

**Route groups (Next.js).** `(auth)` and `(app)` are folders that group pages without changing the URL. Each group gets its own layout.

**Server components vs client components.** Server components (the dashboard guard, `currentUser.ts`) run on the server and can read cookies. Client components (forms, logout button) run in the browser and call the API.

**Proxy (Next.js 16, formerly middleware).** `proxy.ts` runs before a protected page renders. It can redirect, and it can refresh a session and write new cookies.

**Suspense boundary.** Reading cookies or search parameters makes a page dynamic. With Cache Components enabled, that read must sit inside `<Suspense>`, or the build fails. The layouts and pages were written to respect this.

**React `cache()`.** `getCurrentUser` is wrapped so the layout and the dashboard page share one backend call per request.

**Form hook (`useForm`).** One generic hook manages values, validation (shown after blur or submit), submission and errors for every form, including forgot and reset.

**Service boundary (`AuthService`).** Components depend on an interface. Two implementations sit behind it: a real one calling the backend and a mock one (`NEXT_PUBLIC_USE_MOCK_AUTH=true`). Swapping them does not touch the components.

**Silent refresh.** When the access cookie has expired but the refresh cookie is valid, the proxy renews the session during the page request. The user never sees a login screen.

---

## 4. Files created or changed

### Backend (`backend/`)

| File | Purpose |
|---|---|
| `app/main.py` (changed) | Builds the FastAPI app: logging, CORS for `http://localhost:3000` with credentials, rate-limit handler, auth error handler, router, `/` and `/health`. |
| `app/core/config.py` | `Settings` class (pydantic-settings). Reads every environment variable, validates the JWT secret, builds the Azure SQL connection URL. `get_settings()` is cached. |
| `app/core/security.py` | Password hashing and verification (Argon2), JWT create and decode (HS256, type check, pinned algorithm), opaque token generation and SHA-256 hashing. |
| `app/core/time.py` | `utc_now()` and date helpers. All times are naive UTC to match SQL Server's DATETIME2. |
| `app/core/cookies.py` | Names of the two cookies, and functions that set and clear them with the right attributes. |
| `app/core/rate_limit.py` | slowapi `Limiter` keyed by client IP. |
| `app/db/session.py` | Lazy engine (pyodbc, pre-ping, recycle), session factory, `get_db` dependency. |
| `app/db/models.py` | ORM models `User`, `RefreshToken`, `PasswordResetToken` with foreign keys and relationships. |
| `app/schemas/auth.py` | Request and response models with validators: name cleaning, lowercase email, shared password rule. |
| `app/services/auth_service.py` | All business rules: sign-up, authenticate, issue session, refresh with rotation and reuse detection, revoke, request reset, reset password. Raises `AuthError`. |
| `app/services/email_service.py` | Sends reset emails over SMTP, or logs the link in development. Never logs links in production. |
| `app/dependencies/auth.py` | `get_current_user` dependency: reads the access cookie, verifies it, reloads the user, checks `is_active`. |
| `app/api/routes/auth.py` | The `/api/auth` endpoints (signup, login, logout, refresh, forgot-password, reset-password, me) and the error handler. |
| `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` | Alembic configuration; env.py builds the database URL from settings. |
| `alembic/versions/001_create_users.py` | Creates `users`. |
| `alembic/versions/002_create_refresh_tokens.py` | Creates `refresh_tokens` with index on `user_id`. |
| `alembic/versions/003_create_password_reset_tokens.py` | Creates `password_reset_tokens` with index on `user_id`. |
| `scripts/verify_db.py` | Live database check: insert, read back through foreign keys, clean up. |
| `requirements.txt` (changed) | All dependencies pinned with exact versions. |
| `.env.example` | Placeholder template for every setting. Committed. |
| `.env` | Real local values, including the database password and generated JWT secret. Git-ignored. |
| `.gitignore` (changed) | Adds `!.env.example` so the template is committed while `.env` stays ignored. |
| `README.md` (changed) | Setup, migrations, endpoints, layout, security notes. |
| `app/__init__.py` and sub-package `__init__.py` files | Make folders importable packages. |

### Frontend (`frontend/`)

| File | Purpose |
|---|---|
| `proxy.ts` | Protects `/dashboard`. Redirects when there is no session, and silently refreshes an expired access token, writing new cookies. |
| `lib/api/client.ts` (rewritten) | Only HTTP client. Attaches credentials, converts errors to `ApiError` with `code`, refreshes once on a 401 in the browser (shared promise so concurrent 401s do not race), redirects to login if refresh fails. |
| `lib/api/endpoints.ts` | Backend paths in one place. |
| `lib/constants.ts` (changed) | Page routes (`ROUTES`), including forgot and reset, and cookie names (`AUTH_COOKIES`). |
| `types/user.ts` (changed) | `User` with numeric `id`, matching the backend. |
| `features/auth/types/auth.ts` | Form value types and `AuthSession`. Tokens are deliberately absent. |
| `features/auth/utils/validation.ts` | Client-side validation rules, mirroring the backend. Not a security boundary. |
| `features/auth/services/authService.ts` (rewritten) | `AuthService` interface, mock implementation, real implementation, and the switch between them. |
| `features/auth/services/currentUser.ts` | Server-only `getCurrentUser()`: forwards cookies to `/api/auth/me`, redirects to login on failure, cached per request. |
| `features/auth/components/LoginForm.tsx` (changed) | Handles `ACCOUNT_NOT_FOUND` with a Sign Up link carrying the email. |
| `features/auth/components/SignUpForm.tsx` (changed) | Accepts a pre-filled email, handles `EMAIL_TAKEN` with a sign-in link. |
| `features/auth/components/ForgotPasswordForm.tsx` (new) | Email form with the same confirmation for every address. |
| `features/auth/components/ResetPasswordForm.tsx` (new) | New password form; handles missing token, success, and spent or expired token. |
| `features/auth/components/LogoutButton.tsx` (new) | Calls logout, then navigates to login. Stays put and shows an error if logout fails. |
| `app/(auth)/signup/page.tsx` (changed) | Reads `?email=` behind Suspense. |
| `app/(auth)/forgot-password/page.tsx` (new) | Page wrapper. |
| `app/(auth)/reset-password/page.tsx` (new) | Reads `?token=` behind Suspense and passes it to the form. |
| `app/(app)/layout.tsx` (changed) | Synchronous layout; `AuthenticatedShell` inside Suspense performs the session check and renders the header. |
| `app/(app)/dashboard/page.tsx` (changed) | Imports the server-side `getCurrentUser`. |
| `components/layout/AppHeader.tsx` (changed) | Adds the Sign out button. |
| `components/feedback/FullPageLoader.tsx` (new) | Reusable full-page spinner for Suspense fallbacks. |
| `.env.local.example` | Template: API URL and mock switch. Committed. |
| `.env.local` | Local values. Git-ignored. |
| `.gitignore` (changed) | Adds `!.env*.example`. |
| `package.json` (changed) | Adds `server-only@0.0.1`. |

---

## 5. Database design

Database: `Discoveryhub` on Azure SQL. All tables are in schema `dbo`.

**users**
- `id` BIGINT identity, primary key
- `name` NVARCHAR(100), not null
- `email` NVARCHAR(255), not null, unique constraint `uq_users_email`
- `password_hash` NVARCHAR(255), not null
- `is_active` BIT, default 1
- `created_at`, `updated_at` DATETIME2, default `SYSUTCDATETIME()`

**refresh_tokens**
- `id` BIGINT identity, primary key
- `user_id` BIGINT, foreign key to `users.id`, `ON DELETE CASCADE`
- `token_hash` NVARCHAR(128), unique (SHA-256 hex)
- `expires_at` DATETIME2, not null
- `revoked_at` DATETIME2, null while valid
- `created_at` DATETIME2, default `SYSUTCDATETIME()`
- Index `ix_refresh_tokens_user_id` (fast "revoke all for user")

**password_reset_tokens**
- `id` BIGINT identity, primary key
- `user_id` BIGINT, foreign key, `ON DELETE CASCADE`
- `token_hash` NVARCHAR(128), unique
- `expires_at` DATETIME2, not null
- `used_at` DATETIME2, null until spent
- `created_at` DATETIME2, default `SYSUTCDATETIME()`
- Index `ix_password_reset_tokens_user_id`

**Why separate tables?** A user can have many sessions and many reset requests over time. Keeping them apart lets each be revoked and expired independently.

**Why store hashes?** If the database is read by someone else, they get hashes that cannot be turned back into usable tokens.

**Why `SYSUTCDATETIME()` as default?** The database stamps times itself, so a client with a wrong clock cannot write bogus timestamps.

**Shared database discovery.** `neuroxproject` already had a `users` table (different schema, UUID ids), a `sessions` table with 220 rows, and its own Alembic version `0005`. It belongs to another system, so it was left untouched. `Discoveryhub` was confirmed empty, and the backend was pointed there.

---

## 6. Endpoints

All under `/api/auth`. All auth errors use `{"detail": {"code", "message"}}`.

| Method | Path | Input | Success | Main errors |
|---|---|---|---|---|
| POST | `/signup` | name, email, password | 201 user, cookies set | 409 `EMAIL_TAKEN`, 422 validation |
| POST | `/login` | email, password | 200 user, cookies set | 404 `ACCOUNT_NOT_FOUND`, 401 `INVALID_CREDENTIALS`, 403 `ACCOUNT_DISABLED`, 429 `RATE_LIMITED` |
| POST | `/logout` | refresh cookie (optional) | 200, cookies cleared | never fails for a missing cookie |
| POST | `/refresh` | refresh cookie | 200 user, new cookies | 401 `INVALID_REFRESH`, `REFRESH_REUSED`, `REFRESH_RACE` |
| POST | `/forgot-password` | email | 200 generic message | 429, 422 |
| POST | `/reset-password` | token, password | 200 | 400 `INVALID_RESET_TOKEN`, 422 |
| GET | `/me` | access cookie | 200 user | 401 `UNAUTHENTICATED` |

---

## 7. Data flow, step by step

### 7.1 Sign up

1. Browser: `SignUpForm` validates locally, then `authService.signUp` calls `apiRequest` (POST `http://localhost:8000/api/auth/signup`, JSON body, credentials included).
2. Backend, CORS middleware checks the origin is `http://localhost:3000` and allows credentials.
3. Pydantic `SignUpRequest` validates: name cleaned and length-checked, email validated and lowercased, password passes the shared rule.
4. Route `sign_up` calls `auth_service.sign_up`: looks up the email, hashes the password with Argon2, inserts a `User`, commits. A race on the unique constraint is caught and reported as `EMAIL_TAKEN`.
5. `issue_session`: creates a random refresh token, stores its SHA-256 hash in `refresh_tokens`, creates a JWT access token.
6. `set_session_cookies` writes both as HttpOnly cookies on the response.
7. Browser stores the cookies (they belong to `localhost`, so they also apply to port 3000) and receives the user JSON.
8. `LoginForm`/`SignUpForm` navigates to `/dashboard`.

### 7.2 Login

1. `authService.login` posts email and password.
2. `authenticate` finds the user by lowercased email. No user: 404 `ACCOUNT_NOT_FOUND`. Wrong password: 401 generic. Inactive: 403.
3. On success, the same session issuing as sign-up. Cookies are set.
4. The form shows the unknown-email prompt (with a link carrying the email) only for `ACCOUNT_NOT_FOUND`.

### 7.3 Dashboard request (the main protected path)

1. Browser requests `http://localhost:3000/dashboard`, cookies attached automatically.
2. **Proxy** (`proxy.ts`) runs first:
   - Access cookie present → continue.
   - No access and no refresh cookie → redirect to `/login`.
   - Access missing, refresh present → call backend `POST /api/auth/refresh` with the cookie header (5-second timeout).
     - Success: the new `Set-Cookie` headers are copied to the browser response, and the request's `Cookie` header is rewritten with the new access token so the page render sees it.
     - Failure: redirect to `/login` and delete both cookies.
3. The `(app)` layout renders synchronously. `AuthenticatedShell` inside Suspense runs.
4. `getCurrentUser()` reads cookies with `cookies()`, sends them to `GET /api/auth/me` with `cache: "no-store"` and `skipAuthRefresh`, and the backend `get_current_user` dependency verifies the JWT and reloads the user.
5. On 401, `redirect("/login")`. On success, the header and page render with the user's data.
6. The dashboard page calls `getCurrentUser()` again; `React.cache` returns the same result without a second request.

### 7.4 Browser-side refresh (in `lib/api/client.ts`)

1. An authenticated call receives 401.
2. If no refresh is already in progress, one `POST /api/auth/refresh` starts. Other 401s wait on the same promise.
3. If it succeeds, the original request is retried once.
4. If it fails, the browser navigates to `/login`.
5. Auth endpoints (login, signup, refresh, logout, forgot, reset) never trigger this path.

### 7.5 Logout

1. `LogoutButton` calls `authService.logout()` → `POST /api/auth/logout`.
2. Backend revokes the refresh token row (sets `revoked_at`) and clears both cookies with matching attributes.
3. Frontend navigates to `/login` and refreshes the router. If the request fails, it stays put and shows an error.

### 7.6 Forgot password

1. `ForgotPasswordForm` posts the email.
2. Backend checks the rate limit, then `request_password_reset`: cancels older unused reset rows, creates a new token, stores its hash with a 30-minute expiry.
3. Response is always the same generic message. If a token was created, the email is sent in a background task (so timing does not reveal existence).
4. The email contains `{FRONTEND_URL}/reset-password?token=...`. In development with no SMTP, the link is written to the backend log.

### 7.7 Reset password

1. Reset page reads `?token=` on the server (inside Suspense) and passes it to the form.
2. Form posts token and new password.
3. `reset_password` hashes the token, finds the row, checks it is unused and unexpired and the user is active. Any failure returns the same 400.
4. Updates `password_hash`, sets `used_at`, revokes every refresh token for the user, commits.

### 7.8 Refresh rotation and reuse (in `refresh_session`)

1. Find the refresh row by hash.
2. Not found: 401.
3. Already revoked:
   - Revoked within 10 seconds: 401 `REFRESH_RACE` (harmless race, nothing else changes).
   - Revoked longer ago: revoke all of the user's sessions, 401 `REFRESH_REUSED`.
4. Expired or user inactive: 401.
5. Otherwise: revoke this token, create a successor, issue a new access token, commit.

---

## 8. Request and error handling layers

- **Pydantic** rejects malformed input with 422 before business code runs.
- **Service layer** raises `AuthError(status, code, message)`.
- **Exception handler** (`register_auth_error_handler`) turns `AuthError` into the standard JSON.
- **Refresh route** returns its error response directly so the cookie-clearing headers are not lost. (An early version raised instead, which would have discarded them.)
- **Rate limit handler** returns 429 in the same JSON shape.
- **Frontend `client.ts`** converts all shapes (our object, FastAPI validation arrays, plain text, network failure) into `ApiError(status, code, message)`.

---

## 9. Security measures, with reasons

| Measure | Reason |
|---|---|
| Argon2id password hashing | Slow and memory-hard, resistant to GPU guessing. |
| Random 48-byte tokens via `secrets` | Unguessable; `random` module is not cryptographically safe. |
| SHA-256 of tokens in the database | Stolen database rows are not usable tokens. |
| Pinned HS256 algorithm | Blocks `alg: none` and algorithm-confusion attacks. |
| JWT includes `type` claim | A token issued for another purpose cannot be used as an access token. |
| Access token 15 minutes | Limits damage if stolen, since JWTs cannot be revoked instantly. |
| `is_active` checked on every request | A disabled user loses access immediately, not after 15 minutes. |
| Refresh rotation and reuse detection | A stolen refresh token is detected and kills all sessions. |
| Single-use reset tokens, 30-minute expiry | Limits replay and exposure. |
| All sessions revoked on password reset | An attacker's session ends when the owner resets. |
| Generic forgot-password response | Prevents account discovery through that endpoint. |
| Rate limits on login and forgot | Slows guessing and email flooding. |
| HttpOnly, SameSite=Lax cookies; Secure in production | JavaScript cannot read tokens; cross-site requests are restricted; HTTPS only. |
| No tokens in localStorage or sessionStorage | Blocks token theft through injected scripts (verified in the browser test). |
| Logs contain user ids and event names only | No passwords, tokens, or emails in logs (checked by scanning the log files). |
| Reset link logged only in development | Logs are readable by more people than the mailbox owner. |
| Secret must be 32+ characters, not a placeholder | Server refuses to start with a weak signing key. |
| Forms use `method="post"` | Credentials never end up in URLs, history, or server logs, even before JavaScript loads. |
| Server-only session code (`server-only` package) | Build fails if the session logic is imported into the browser bundle. |
| Parameterised queries (SQLAlchemy) | Prevents SQL injection. |

---

## 10. Configuration

Backend settings come from `backend/.env` (see `.env.example`):

- `ENVIRONMENT`, `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER`
- `JWT_SECRET_KEY` (generated with `secrets.token_urlsafe(64)`)
- `FRONTEND_URL`, `COOKIE_SECURE`, `COOKIE_SAMESITE`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`
- `LOGIN_RATE_LIMIT`, `FORGOT_PASSWORD_RATE_LIMIT`

Frontend settings come from `frontend/.env.local`:

- `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)
- `NEXT_PUBLIC_USE_MOCK_AUTH` (`true` for mock, `false` for real)

Token lifetimes are fixed in settings: access 15 minutes, refresh 30 days, reset 30 minutes, reuse grace window 10 seconds.

---

## 11. Problems encountered and how they were solved

1. **`uvicorn main:app` failed with WinError 10013.** Port 8000 was held by a leftover Python process, and the module path was wrong (the app is `app.main:app`). Fixed by using the right path and another port for the test; later the port was freed.
2. **Azure SQL login timed out, then "database not currently available".** The database was not yet online (serverless resume). Retried in a loop until it connected.
3. **Alembic reported revision `0005`.** `neuroxproject` had another system's migration history. Investigated read-only, found it was live data, did not modify it, and used the empty `Discoveryhub` database instead.
4. **`cookies()` in a layout broke the build.** Cache Components requires request-time reads to sit inside Suspense. Moved the session check into a Suspense-wrapped component.
5. **`searchParams` broke the build for `/signup`.** Same rule. The page now passes the promise down and the child awaits it inside Suspense.
6. **Email appeared twice on the page after navigating from login.** Not a bug: Next keeps visited pages mounted but hidden (`display: none`). Test locators were changed to match only visible elements.
7. **Credentials appeared in the URL.** A click before hydration submitted the form as a GET. Fixed with `method="post"` on all auth forms.
8. **Dashboard browser test timed out.** The dev server was still compiling; the test was given longer timeouts and waits for network idle.
9. **Rate limit fired after 3 requests in one test run.** The count came from an older server instance still holding counts; a fresh restart showed exactly 5 allowed.
10. **Concurrent refresh could log users out.** Two requests with the same refresh token would look like theft. Added a 10-second grace window and in-browser refresh deduplication.
11. **`redirect()` inside `try` would have been swallowed.** Structured `getCurrentUser` so `redirect()` is called in the `catch` block, outside the `try`.
12. **Refresh failure lost the cookie-clearing headers.** Returned the error response directly instead of raising.
13. **`.env.example` was ignored by git.** The `.env.*` rule matched the template too. Added negations in both `.gitignore` files.
14. **Frontend had a `getCurrentUser` that could not see cookies from the browser.** Moved the server-side read into its own file.
15. **Port 3000 held by a `next dev` process.** Identified it and did not stop it (it may belong to another workflow); tests ran against it.

---

## 12. Known limitations and decisions to review

- **Account enumeration on login.** `ACCOUNT_NOT_FOUND` reveals which emails are registered. This was specified by the product requirement. The rate limit reduces the risk but does not remove it.
- **Google sign-in** returns "not available yet". The backend has no Google flow.
- **Client-side refresh path** (`client.ts`) is implemented but no current screen exercises it; it is untested in a browser.
- **Production build** compiles but was not served in a browser; the browser tests ran against the dev server.
- **Reset links in development** are written to the backend log. Configure SMTP for real use.
- **Production cookies** require the frontend and backend to be on the same site (same registrable domain) for SameSite=Lax to send them across ports or subdomains. Local development uses `localhost`.
- **Database password** was shared in chat during setup; rotate it.
- **Shared database** `neuroxproject` belongs to another system; confirm `Discoveryhub` is the intended database.
- **Python minimum version** is not verified; the README says 3.14, which is what was used.
- **npm audit** reported vulnerabilities during install; not reviewed.
- **Nothing is committed** to git yet.
- **Timing side channel** on forgot-password remains (existing accounts do database writes, unknown ones return early).

---

## 13. Testing

### 13.1 Test files

| File | Type | How to run | Checks |
|---|---|---|---|
| `backend/scripts/verify_db.py` (in repo) | Database check | `python scripts/verify_db.py` from `backend/` | Insert, read back through foreign keys, clean up. |
| `scratchpad/e2e_auth.py` (outside repo) | API end-to-end | Backend running with relaxed limits (`LOGIN_RATE_LIMIT=100/minute`, `FORGOT_PASSWORD_RATE_LIMIT=100/minute`) | 29 checks: validation, sign-up, duplicate, me, logout, login errors, rotation, race grace, reuse detection, forgot generic, reset, single-use, old password rejected, garbage token. |
| `scratchpad/e2e-ui/ui_flow.js` (outside repo) | Browser end-to-end (Playwright) | Backend on 8000, frontend on 3000 | 24 checks: redirects, sign-up, cookies, storage, sign-out, unknown email, wrong password, login, forgot, reset, reuse, silent refresh, bogus session. |
| Static checks | Compile and lint | `npx tsc --noEmit`, `npm run lint`, `npm run build` | Types, lint rules, production build. |
| Rate-limit probe | Manual | Six login attempts with curl or PowerShell | Confirms 5 allowed, 6th returns 429. |
| Log scan | Manual | Search `uv_err.log` for password literals and the JWT secret | Confirms no secrets logged. |

Scratch-folder debugging scripts (`inspect_db.py`, `inspect_users.py`, `list_dbs.py`, `check_discoveryhub.py`, `debug_*.js`) were used during investigation and are not test suites.

### 13.2 Results

- verify_db: passed.
- API e2e: 29 of 29 passed.
- Browser e2e: 24 of 24 passed (two consecutive runs).
- Rate limit: exactly 5 allowed, then 429.
- Build, type check and lint: passed.

### 13.3 Test checklist for manual use

- [ ] Visiting `/dashboard` without a session redirects to `/login`.
- [ ] Sign up with a new email lands on `/dashboard` with the name in the header.
- [ ] Cookies `access_token` and `refresh_token` are HttpOnly and not in localStorage.
- [ ] Sign out returns to `/login`, removes cookies, and `/dashboard` is protected again.
- [ ] Login with an unknown email shows "No account exists" and a link that opens Sign Up with the email filled in.
- [ ] Login with a wrong password shows "Incorrect email or password".
- [ ] Correct login lands on `/dashboard`.
- [ ] Forgot password shows the same confirmation for a known and an unknown email.
- [ ] The reset link (from the backend log in development) sets a new password.
- [ ] Reusing the same reset link is rejected.
- [ ] The old password is rejected after reset, and the new one works.
- [ ] Deleting only the access cookie and visiting `/dashboard` still loads the dashboard (silent refresh).
- [ ] A bogus refresh cookie redirects to `/login` and clears cookies.
- [ ] Six login attempts within a minute from one IP return 429 on the sixth.

---

## 14. How to run

```powershell
# Backend (from backend/)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python scripts/verify_db.py
uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/)
npm install
npm run dev        # http://localhost:3000
```

Interactive API documentation: `http://localhost:8000/docs`.

---

## 15. Glossary

- **ASGI**: the async interface between a Python web framework and its server.
- **Argon2id**: memory-hard password hashing algorithm, winner of the Password Hashing Competition.
- **Cache Components**: Next.js 16 mode where pages are prerendered and request-time reads stream in behind Suspense.
- **Cookie (HttpOnly / Secure / SameSite)**: a small value the browser stores and sends back automatically; HttpOnly hides it from JavaScript, Secure restricts it to HTTPS, SameSite limits cross-site sending.
- **CORS**: browser rule that restricts cross-origin requests; the backend allows only the frontend origin.
- **Dependency injection**: FastAPI passes resources (database session, current user) into route functions.
- **Hydration**: when React attaches event handlers to server-rendered HTML.
- **Idempotent**: safe to repeat; logout is idempotent.
- **JWT (JSON Web Token)**: signed token containing claims; verified by signature, not by a database lookup.
- **Migration**: a versioned, reversible change to the database schema.
- **Opaque token**: a random string with no meaning of its own; the server looks it up.
- **ORM**: object-relational mapper; maps Python classes to tables.
- **Pool pre-ping**: checks a pooled connection before use.
- **Proxy (Next.js)**: code that runs before a request is rendered; formerly called middleware.
- **Rate limiting**: capping requests per time window per client.
- **Refresh rotation**: each refresh token is used once and replaced.
- **Reuse detection**: noticing a revoked refresh token being presented again.
- **Server-only**: a marker that makes a module refuse to load in the browser.
- **Suspense**: React boundary that shows a fallback while async content loads.
- **SameSite**: cookie attribute controlling cross-site sending; Lax allows top-level navigation only.
- **SHA-256**: fast cryptographic hash; used here for tokens, not passwords.
- **Single-use token**: marked as used on first success and rejected afterwards.

---

## 16. Timeline of the build

1. Read the Next.js 16 bundled documentation (cookies, proxy, Cache Components authentication guide).
2. Confirmed the local environment: Python 3.14.6, ODBC Driver 18, Node 24, Azure SQL reachable.
3. Installed backend dependencies and pinned the versions.
4. Wrote configuration, security, time, cookies, rate-limit, database session and model modules.
5. Wrote schemas, services, dependencies, routes and the application entry point.
6. Created `.env` with a generated JWT secret; found Azure database paused, waited for it to resume.
7. Discovered `neuroxproject` was shared and in use; used `Discoveryhub` instead.
8. Wrote three Alembic migrations and ran `alembic upgrade head` successfully.
9. Wrote and ran `verify_db.py`; fixed a bug where inserts were never committed.
10. Started the backend and ran the 29-check API test; fixed the refresh-response bug found while writing it.
11. Verified the rate limit and scanned logs for secrets.
12. Wrote the frontend layer: constants, endpoints, HTTP client, types, validation, service boundary, server user read.
13. Wrote the proxy for silent refresh and dashboard protection.
14. Updated the auth forms, added forgot and reset pages and the logout button, and reworked the dashboard layout.
15. Ran type check, lint and build; fixed two Suspense errors reported by the build.
16. Installed the Playwright test environment in the scratch folder and ran the browser flow.
17. Fixed the POST form issue, the hidden-page test selectors, and test timing; reran until 24 of 24 passed.
18. Verified no secrets are in committable files; left the backend running on port 8000.

---

## 17. Files changed outside the auth feature

- `frontend/app/globals.css`, `frontend/app/layout.tsx`, `frontend/app/styles/tokens.css` (design system, from earlier work).
- `frontend/app/page.tsx` was deleted earlier; the `/` to `/login` redirect is in `next.config.ts`.
- `frontend/next.config.ts` (redirect and Cache Components settings, from earlier work).
- `.claude/skills/ui-design-system/SKILL.md` (project skill, from earlier work).

