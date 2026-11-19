# DiscoveryHub Project Overview

## Executive Summary

**DiscoveryHub** is a full-stack web application designed to help users discover, organize, and manage research projects. The application features:

- **Authentication System**: Sign up, login, logout, refresh tokens, password reset with email verification
- **Project Management**: Create, edit, and list projects with metadata (name, description, dates)
- **User Isolation**: Projects are scoped to their owners with strict access controls
- **Modern Architecture**: FastAPI backend (Python) + Next.js frontend (TypeScript) + Azure SQL database

The application enforces role-based access (owner can only see/edit their own projects) and provides a responsive UI across desktop and mobile.

---

## Architecture Overview

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Next.js | 16.4.5 |
| **Frontend Language** | TypeScript + React | Latest |
| **Frontend Styling** | Tailwind CSS | v4 |
| **Backend** | FastAPI | Latest |
| **Backend Language** | Python | 3.11+ |
| **Database** | Azure SQL (MSSQL) | Latest |
| **ORM** | SQLAlchemy | 2.1 |
| **Migrations** | Alembic | Latest |
| **Authentication** | JWT (HS256) + Cookies | Custom |
| **Testing** | pytest (backend), Playwright (e2e) | Latest |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / Client                      │
├─────────────────────────────────────────────────────────────┤
│                    Next.js Frontend (3001)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Pages: auth, dashboard, project overview           │   │
│  │  Components: UI primitives, forms, modals            │   │
│  │  Hooks: useForm, authentication                      │   │
│  │  Services: API client, server-side data fetching     │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  HTTP/HTTPS (cookies carry JWT access token)               │
├─────────────────────────────────────────────────────────────┤
│                  FastAPI Backend (8000/8001)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routes: /api/auth, /api/projects                   │   │
│  │  Middleware: CORS, rate limiting, auth checks       │   │
│  │  Services: business logic, validation, email        │   │
│  │  Database: SQLAlchemy ORM + Alembic migrations      │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│            Azure SQL "Discoveryhub" Database               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tables: users, refresh_tokens, password_resets,     │   │
│  │         projects                                     │   │
│  │ Keys: PK, FK CASCADE, CHECK constraints, indexes    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

### Root Level

```
DiscoveryHub/
├── backend/                    # FastAPI application (Python)
├── frontend/                   # Next.js application (TypeScript)
├── .claude/                    # Claude Code configuration & skills
├── .git/                       # Git repository
├── .gitignore                  # Version control ignore rules
├── README.md                   # Project root documentation
├── Creation-of-Auth-System.md  # Auth system documentation
└── PROJECT_OVERVIEW.md         # This file
```

---

## Backend Directory Structure

### `backend/` - FastAPI Application

```
backend/
├── .venv/                      # Virtual environment (git-ignored)
├── .env                        # Environment variables (git-ignored)
├── .env.example                # Template for environment variables
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies (pytest, httpx)
├── pyproject.toml              # Python project metadata
│
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                 # **ENTRY POINT**: FastAPI app factory
│   │                            # - Creates app instance
│   │                            # - Configures CORS (allow methods: GET, POST, PATCH)
│   │                            # - Sets up rate limiting middleware
│   │                            # - Includes routers: auth, projects
│   │
│   ├── core/                   # Configuration and security utilities
│   │   ├── __init__.py
│   │   ├── config.py           # **ENVIRONMENT CONFIG**
│   │   │                        # - Reads .env variables (DATABASE_URL, JWT_SECRET_KEY, etc.)
│   │   │                        # - Validates required settings
│   │   │                        # - Settings class: Settings (pydantic)
│   │   │
│   │   ├── security.py         # **PASSWORD & TOKEN HASHING**
│   │   │                        # - hash_password(): Argon2id hashing
│   │   │                        # - verify_password(): constant-time comparison
│   │   │                        # - hash_token(): SHA-256 for refresh/reset tokens
│   │   │                        # - Ensures raw passwords never stored
│   │   │
│   │   ├── cookies.py          # **COOKIE CONSTANTS**
│   │   │                        # - ACCESS_COOKIE: "access_token"
│   │   │                        # - REFRESH_COOKIE: "refresh_token"
│   │   │                        # - Settings: HttpOnly=True, SameSite=Lax
│   │   │
│   │   ├── time.py             # **TIME UTILITIES**
│   │   │                        # - utc_now(): returns current UTC time
│   │   │                        # - Used for token expiry, timestamps
│   │   │
│   │   └── rate_limit.py       # **RATE LIMITING**
│   │                            # - Middleware to prevent abuse
│   │                            # - Tracks requests per IP/user
│   │
│   ├── db/                     # Database connection and models
│   │   ├── __init__.py
│   │   ├── session.py          # **DATABASE SESSION FACTORY**
│   │   │                        # - get_session_factory(): returns SQLAlchemy session factory
│   │   │                        # - Connects to Azure SQL via pyodbc
│   │   │                        # - URL: mssql+pyodbc://...
│   │   │
│   │   └── models.py           # **ORM MODELS** (SQLAlchemy)
│   │                            # Core tables:
│   │                            # - User: id, full_name, email (unique), password_hash, created_at
│   │                            # - RefreshToken: id, user_id (FK), token_hash, expires_at
│   │                            # - PasswordResetToken: id, user_id (FK), token_hash, expires_at
│   │                            # - Project: id, owner_id (FK), name, description, start_date,
│   │                            #            end_date, created_at, updated_at
│   │                            #   Constraints: CHECK (end_date >= start_date), 
│   │                            #               INDEX (owner_id, created_at)
│   │
│   ├── api/                    # HTTP endpoints (FastAPI routers)
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py         # **AUTH ENDPOINTS**
│   │       │                    # POST   /api/auth/signup        - Create account (201)
│   │       │                    # POST   /api/auth/login         - Sign in (200)
│   │       │                    # POST   /api/auth/logout        - End session (200)
│   │       │                    # POST   /api/auth/refresh       - Rotate token (200)
│   │       │                    # POST   /api/auth/forgot-password - Send reset link
│   │       │                    # POST   /api/auth/reset-password  - Set new password
│   │       │                    # GET    /api/auth/me            - Current user info (200/401)
│   │       │
│   │       └── projects.py     # **PROJECT ENDPOINTS**
│   │                            # POST   /api/projects           - Create (201, owner's id)
│   │                            # GET    /api/projects           - List (200, owner's projects)
│   │                            #        ?limit=5              - Max 50 results
│   │                            # GET    /api/projects/{id}      - Get single (200/404)
│   │                            # PATCH  /api/projects/{id}      - Update (200/404/422)
│   │                            #        - Only owner can edit
│   │                            #        - Returns 404 for missing or foreign projects
│   │                            #        - Validates date order (422 INVALID_DATE_RANGE)
│   │
│   ├── schemas/                # Request/response models (Pydantic v2)
│   │   ├── __init__.py
│   │   ├── auth.py             # **AUTH SCHEMAS**
│   │   │                        # - SignUpRequest: full_name, email, password, confirm_password
│   │   │                        # - LoginRequest: email, password
│   │   │                        # - UserRead: id, full_name, email, created_at
│   │   │                        # - AuthResponse: user, access_token, refresh_token (expiry)
│   │   │
│   │   └── project.py          # **PROJECT SCHEMAS**
│   │                            # - ProjectCreate: name, description, start_date, end_date
│   │                            #   Validators: clean_name, clean_description, check_date_order
│   │                            # - ProjectUpdate: name?, description?, start_date?, end_date?
│   │                            #   Validators: same as Create (optional fields)
│   │                            # - ProjectRead: id, name, description, owner_id, owner_name,
│   │                            #               start_date, end_date, created_at (+UTC offset),
│   │                            #               updated_at (+UTC offset)
│   │
│   ├── services/               # Business logic and workflows
│   │   ├── __init__.py
│   │   ├── auth_service.py     # **AUTH SERVICE**
│   │   │                        # Functions:
│   │   │                        # - sign_up(db, name, email, pwd) → User
│   │   │                        # - issue_session(db, user) → Session (access + refresh tokens)
│   │   │                        # - login(db, email, pwd) → Session
│   │   │                        # - logout(db, session) → revokes refresh token
│   │   │                        # - refresh_access_token(db, refresh_token) → Session (rotates)
│   │   │                        # - send_password_reset_email(user) → logs to stdout
│   │   │                        # - reset_password(db, token, new_pwd) → revokes all sessions
│   │   │                        # - Token lifetime: access 15m, refresh 30d
│   │   │
│   │   ├── email_service.py    # **EMAIL SERVICE**
│   │   │                        # - send_email_stub(): placeholder for production email
│   │   │                        # - Logs to stdout in dev; integrates with SendGrid in prod
│   │   │
│   │   └── project_service.py  # **PROJECT SERVICE**
│   │                            # Functions:
│   │                            # - create_project(db, owner, payload) → Project (201)
│   │                            # - list_projects(db, owner_id, limit) → Project[]
│   │                            #   Ordered by updated_at DESC, then id DESC
│   │                            # - get_project(db, owner_id, id) → Project or None
│   │                            #   Returns None if missing or foreign (404)
│   │                            # - update_project(db, owner_id, id, payload) → Project
│   │                            #   Validates dates before mutation; raises 422 if invalid
│   │                            # - _to_read(project, user): helper to serialize with owner_name
│   │
│   └── dependencies/           # Dependency injection for endpoints
│       ├── __init__.py
│       └── auth.py             # **CURRENT USER DEPENDENCY**
│                                # - get_current_user(request, db) → CurrentUser
│                                # - Reads access token from cookie
│                                # - Verifies JWT signature and expiry
│                                # - Raises 401 UNAUTHENTICATED if missing/invalid
│                                # - CurrentUser = dataclass(id, full_name, email)
│
├── alembic/                    # Database migrations (Alembic)
│   ├── env.py                  # **MIGRATION CONFIG**
│   │                            # - Alembic runtime configuration
│   │                            # - Reads DATABASE_URL and creates connection
│   │                            # - Target metadata points to models.py
│   │
│   ├── alembic.ini             # Alembic config file (main)
│   │
│   └── versions/               # Migration scripts (ordered by revision number)
│       ├── 001_create_users.py
│       │   # Creates users table
│       │   # Columns: id (BIGINT identity), full_name, email, password_hash, created_at
│       │   # Constraints: PK(id), UNIQUE(email), INDEX(created_at)
│       │
│       ├── 002_create_refresh_tokens.py
│       │   # Creates refresh_tokens table (rotation-based session management)
│       │   # Columns: id, user_id (FK → users), token_hash, expires_at, created_at
│       │   # Constraints: FK CASCADE, INDEX(user_id)
│       │
│       ├── 003_create_password_reset_tokens.py
│       │   # Creates password_reset_tokens table (one-time reset links)
│       │   # Columns: id, user_id (FK → users), token_hash, expires_at, created_at
│       │   # Constraints: FK CASCADE, INDEX(user_id, created_at)
│       │
│       └── 004_create_projects.py
│           # Creates projects table (new feature)
│           # Columns: id (BIGINT identity), owner_id (FK → users),
│           #          name (NVARCHAR 255), description (NVARCHAR max),
│           #          start_date (DATE NULL), end_date (DATE NULL),
│           #          created_at (DATETIME2 UTC), updated_at (DATETIME2 UTC)
│           # Constraints: PK(id), FK CASCADE, CHECK (end_date >= start_date),
│           #              INDEX(owner_id, created_at)
│
├── tests/                      # Pytest test suite
│   └── test_projects.py        # **PROJECT TESTS** (12 test cases)
│                                # - Fixtures: make_user (creates real user with session)
│                                # - Tests cover:
│                                #   * Create with details, UTC offset on timestamps
│                                #   * Empty description → null
│                                #   * List isolation by owner, ordered by recency, limit
│                                #   * Get returns 404 for missing/foreign
│                                #   * Date range validation (422)
│                                #   * Blank name validation (422)
│                                #   * Update mutates fields, updates timestamp
│                                #   * Partial update checked against stored start_date
│                                #   * Update returns 404 for foreign
│                                #   * Auth required (401 UNAUTHENTICATED)
│
├── scripts/                    # Utility scripts
│   └── verify_db.py            # **DB VERIFICATION**
│                                # - Connects to Azure SQL and inspects schema
│                                # - Lists tables, columns, foreign keys, indexes
│                                # - Validates schema matches models.py
│
└── README.md                   # Backend setup and endpoint docs
```

### Key Backend Patterns

**Authentication Flow:**
1. User signs up → password hashed with Argon2id → stored in DB
2. User logs in → password verified → access + refresh tokens issued
3. Access token (JWT, 15m expiry) sent as HttpOnly cookie on every request
4. Refresh token (30d expiry) used to rotate and get new access token
5. Password reset: one-time token sent via email, expires in 24h

**Project Isolation:**
- `get_current_user()` dependency extracts user from JWT cookie
- `project_service.get_project()` checks `owner_id == current_user.id`
- Missing or foreign projects → `404 PROJECT_NOT_FOUND` (never `403`)

**Error Response Shape:**
```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

---

## Frontend Directory Structure

### `frontend/` - Next.js Application

```
frontend/
├── node_modules/               # Dependencies (npm, git-ignored)
├── .next/                      # Build artifacts (git-ignored)
├── public/                     # Static assets
│   ├── brand/                  # Company branding
│   │   ├── c5i-logo.png       # Main logo
│   │   └── c5i-logo-light.png # Light theme variant
│   └── *.svg                   # Icon files
│
├── app/                        # **NEXT.JS APP ROUTER**
│   ├── layout.tsx              # **ROOT LAYOUT**
│   │                            # - Sets <html>, <head>, providers
│   │                            # - Imports fonts (Geist Sans/Mono)
│   │                            # - Configures Tailwind CSS (v4 @theme)
│   │
│   ├── globals.css             # **GLOBAL STYLES & TOKENS**
│   │                            # - Tailwind configuration with @theme
│   │                            # - Design tokens: colors, spacing, typography
│   │                            # - Custom tokens: --color-surface-overlay (modal backdrop)
│   │                            # - No hard-coded hex colors; all from variables
│   │
│   ├── (auth)/                 # **AUTH LAYOUT GROUP** (no padding/shell)
│   │   ├── layout.tsx          # Centered auth layout
│   │   ├── signup/
│   │   │   └── page.tsx        # **SIGNUP PAGE**
│   │   │                        # - Shows SignUpForm
│   │   │                        # - Form: name, email, password, confirm password
│   │   │                        # - On success: signs up, logs in, redirects to /dashboard
│   │   │                        # - Route: GET /signup
│   │   │
│   │   └── login/
│   │       └── page.tsx        # **LOGIN PAGE**
│   │                            # - Shows LoginForm
│   │                            # - Form: email, password
│   │                            # - On success: signs in, redirects to /dashboard
│   │                            # - Route: GET /login
│   │
│   ├── (app)/                  # **MAIN LAYOUT GROUP** (with AppHeader + shell)
│   │   ├── layout.tsx          # **APP LAYOUT**
│   │   │                        # - Requires authentication (redirects to /login if not)
│   │   │                        # - Renders AppHeader with current user
│   │   │                        # - Wraps children with AuthProvider
│   │   │
│   │   ├── (main)/             # **MAIN ROUTES** (dashboard, etc.)
│   │   │   └── dashboard/
│   │   │       ├── page.tsx    # **DASHBOARD PAGE**
│   │   │       │                # - Shows welcome message
│   │   │       │                # - "Create New Project" button (CreateProjectButton)
│   │   │       │                # - RecentProjects component (lists 5 most recent)
│   │   │       │                # - QuickAccessItems (static links to features)
│   │   │       │                # - Empty state: "No projects yet"
│   │   │       │                # - Route: GET /dashboard (protected)
│   │   │       │
│   │   │       └── loading.tsx # Loading skeleton for dashboard
│   │   │
│   │   └── (project)/          # **PROJECT-SCOPED ROUTES**
│   │       └── projects/
│   │           └── [projectId]/
│   │               ├── layout.tsx  # **PROJECT LAYOUT**
│   │               │                # - Fetches project for current user
│   │               │                # - Shows AppHeader with project name
│   │               │                # - Renders ProjectSubNav (breadcrumb)
│   │               │                # - Calls notFound() if missing or foreign
│   │               │
│   │               └── overview/
│   │                   ├── page.tsx # **PROJECT OVERVIEW PAGE**
│   │                   │             # - Shows ProjectSummaryCard (name, description, dates)
│   │                   │             # - Shows SourcesCard ("Document upload coming soon")
│   │                   │             # - EditProjectButton to modify project
│   │                   │             # - Lists: owner, created, last updated
│   │                   │             # - Route: GET /projects/{id}/overview
│   │                   │
│   │                   ├── loading.tsx  # Loading skeleton for overview
│   │                   └── error.tsx    # Error boundary
│   │
│   └── middleware.ts           # **NEXT.JS MIDDLEWARE** (optional)
│                                # - Request/response interception
│                                # - Auth token refresh check
│                                # - Redirect unauthenticated users to /login
│
├── components/                 # **REUSABLE UI COMPONENTS**
│   ├── ui/                     # **DESIGN SYSTEM PRIMITIVES**
│   │   ├── Button.tsx          # Button with variants (primary, outline, secondary)
│   │   ├── Input.tsx           # Text input with error state
│   │   ├── Textarea.tsx        # Multi-line text input
│   │   ├── Modal.tsx           # Native <dialog> element wrapper
│   │   ├── Badge.tsx           # Small label/status indicator
│   │   ├── Checkbox.tsx        # Toggle control
│   │   ├── FormField.tsx       # Label + input wrapper (with required badge)
│   │   ├── ErrorBoundary.tsx   # React error boundary
│   │   ├── ErrorState.tsx      # Full-page error UI
│   │   ├── EmptyState.tsx      # Full-page empty state (no data)
│   │   ├── SectionCard.tsx     # Content card/box
│   │   ├── Alert.tsx           # Alert message (success, error, warning)
│   │   ├── Skeleton.tsx        # Loading placeholder
│   │   └── Icon files (*.tsx)   # Icon components (PlusIcon, ArrowRightIcon, etc.)
│   │
│   ├── layout/                 # **LAYOUT COMPONENTS**
│   │   ├── AppHeader.tsx       # Top navigation bar (logo, user menu, logout)
│   │   └── AppShell.tsx        # Layout wrapper
│   │
│   └── brand/                  # **BRANDING COMPONENTS**
│       └── Logo.tsx            # C5i logo with light/dark variants
│
├── features/                   # **FEATURE MODULES** (domain-specific code)
│   ├── auth/                   # **AUTHENTICATION FEATURE**
│   │   ├── services/
│   │   │   ├── currentUser.ts  # **GET CURRENT USER** (server-only)
│   │   │   │                    # - Reads session from cookies
│   │   │   │                    # - Returns CurrentUser or redirects to /login
│   │   │   │
│   │   │   └── authService.ts  # **AUTH API CALLS** (browser)
│   │   │                        # - signUp(data) → calls POST /api/auth/signup
│   │   │                        # - login(data) → calls POST /api/auth/login
│   │   │                        # - logout() → calls POST /api/auth/logout
│   │   │                        # - me() → calls GET /api/auth/me
│   │   │
│   │   ├── types/
│   │   │   └── auth.ts         # TypeScript types: SignUpData, LoginData, User, etc.
│   │   │
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx # React context for auth state (optional)
│   │   │
│   │   └── components/
│   │       ├── SignUpForm.tsx  # **SIGNUP FORM**
│   │       │                    # - Fields: full name, email, password, confirm password
│   │       │                    # - Client-side validation
│   │       │                    # - Calls authService.signUp()
│   │       │                    # - Shows inline errors
│   │       │
│   │       ├── LoginForm.tsx   # **LOGIN FORM**
│   │       │                    # - Fields: email, password, "remember me"?
│   │       │                    # - Client-side validation
│   │       │                    # - Calls authService.login()
│   │       │                    # - Shows inline errors
│   │       │
│   │       ├── ForgotPasswordForm.tsx  # Forgot password flow
│   │       ├── ResetPasswordForm.tsx   # Reset password with token
│   │       └── LogoutButton.tsx        # Simple logout trigger
│   │
│   ├── projects/               # **PROJECTS FEATURE**
│   │   ├── types/
│   │   │   └── projectForm.ts  # ProjectFormValues type
│   │   │
│   │   ├── utils/
│   │   │   ├── validation.ts   # **PROJECT VALIDATION**
│   │   │   │                    # - validateProjectForm(): name, description, dates
│   │   │   │                    # - PROJECT_DESCRIPTION_MAX_LENGTH = 5000
│   │   │   │
│   │   │   └── projectInput.ts # **DATA TRANSFORMATION**
│   │   │                        # - toProjectInput(): trim, blank → null
│   │   │                        # - toFormValues(): format dates as YYYY-MM-DD
│   │   │
│   │   ├── services/
│   │   │   ├── projectService.ts    # **PROJECT API CALLS** (browser)
│   │   │   │                         # - createProject(data) → POST /api/projects
│   │   │   │                         # - updateProject(id, data) → PATCH /api/projects/{id}
│   │   │   │                         # - Uses apiRequest<T>() helper
│   │   │   │
│   │   │   └── serverProjectService.ts # **SERVER-SIDE PROJECT LOGIC**
│   │   │       (import "server-only")  # - listRecentProjects(limit)
│   │   │                               # - getProjectForCurrentUser(id)
│   │   │                               # - requireProjectForCurrentUser(id)
│   │   │                               # - Forwards cookies() to API
│   │   │                               # - Handles session errors (redirects to /login)
│   │   │
│   │   └── components/
│   │       ├── ProjectForm.tsx        # **PROJECT FORM**
│   │       │                           # - Fields: name, description, start/end dates
│   │       │                           # - Uses useForm hook
│   │       │                           # - Shows inline validation errors
│   │       │                           # - Description counter: "X / 5,000"
│   │       │                           # - Cancel and submit buttons
│   │       │
│   │       ├── ProjectFormModal.tsx   # **PROJECT FORM MODAL**
│   │       │                           # - Wraps ProjectForm in Modal
│   │       │                           # - Title: "Create a new project" or "Edit project"
│   │       │                           # - Submit label: "Continue" or "Save changes"
│   │       │                           # - Calls onSaved(project) on success
│   │       │
│   │       ├── CreateProjectButton.tsx # **CREATE BUTTON**
│   │       │                            # - Opens ProjectFormModal
│   │       │                            # - On save: redirects to project overview
│   │       │                            # - Customizable label
│   │       │
│   │       └── EditProjectButton.tsx   # **EDIT BUTTON**
│   │                                   # - Opens ProjectFormModal (edit mode)
│   │                                   # - Takes project as prop
│   │                                   # - On save: closes modal, refreshes data
│   │
│   ├── dashboard/              # **DASHBOARD FEATURE**
│   │   ├── types/
│   │   │   └── dashboard.ts    # Dashboard, QuickAccessItem, DashboardData types
│   │   │
│   │   ├── services/
│   │   │   └── dashboardService.ts # **DASHBOARD DATA**
│   │   │                            # - listRecentProjects(limit)
│   │   │                            # - QUICK_ACCESS_ITEMS (static)
│   │   │
│   │   ├── data/
│   │   │   └── quickAccessItems.ts # Static quick-access links
│   │   │
│   │   └── components/
│   │       ├── RecentProjects.tsx   # **PROJECTS LIST**
│   │       │                         # - Grid of ProjectCard
│   │       │                         # - Shows "No projects yet" if empty
│   │       │                         # - emptyAction prop (e.g., CreateProjectButton)
│   │       │
│   │       ├── ProjectCard.tsx      # **PROJECT CARD**
│   │       │                         # - Shows: name, description, last updated
│   │       │                         # - Links to overview page
│   │       │                         # - Used in RecentProjects and dashboard
│   │       │
│   │       ├── QuickAccess.tsx      # Quick-access links (features, docs, etc.)
│   │       └── DashboardSkeleton.tsx # Loading skeleton
│   │
│   └── project-overview/       # **PROJECT OVERVIEW FEATURE**
│       ├── types/
│       │   └── projectOverview.ts   # Types (if needed)
│       │
│       ├── utils/
│       │   └── formatProjectDate.ts # **DATE FORMATTING**
│       │                             # - formatProjectDate(YYYY-MM-DD) → "1 Nov 2026"
│       │                             # - formatProjectTimestamp(ISO) → "1 Nov 2026, 14:30"
│       │
│       ├── services/
│       │   └── projectOverviewService.ts # **OVERVIEW DATA** (unused/deprecated)
│       │
│       ├── data/
│       │   └── mockProjectOverview.ts # Mock data (unused/deprecated)
│       │
│       └── components/
│           ├── ProjectSummaryCard.tsx # **SUMMARY CARD**
│           │                           # - Name, description, owner
│           │                           # - Dates: start, end, created, updated
│           │                           # - Edit button
│           │
│           └── SourcesCard.tsx        # **SOURCES CARD** (disabled)
│                                       # - Shows "Document upload coming soon"
│                                       # - aria-disabled="true"
│                                       # - Placeholder for future feature
│
├── hooks/                      # **CUSTOM REACT HOOKS**
│   ├── useForm.ts              # **FORM MANAGEMENT**
│   │                            # - Manages form state, errors, submission
│   │                            # - Fields: name, email, password, etc.
│   │                            # - Handles validation, blur, change events
│   │                            # - Accepts HTMLInputElement | HTMLTextAreaElement
│   │                            # - Returns: values, errors, isSubmitting, handleSubmit, etc.
│   │
│   └── useAuth.ts (if exists)   # Auth state management (optional)
│
├── lib/                        # **UTILITIES & HELPERS**
│   ├── api/
│   │   ├── client.ts           # **API REQUEST HELPER**
│   │   │                        # - apiRequest<T>(path, options)
│   │   │                        # - Handles JSON parsing, error responses
│   │   │                        # - Sets correct Content-Type headers
│   │   │                        # - Uses fetch() with credentials: "include"
│   │   │
│   │   └── endpoints.ts        # **API ROUTES REFERENCE**
│   │                            # - endpoints.auth.* (signup, login, logout, me)
│   │                            # - endpoints.projects.* (list, detail, create, update)
│   │
│   ├── constants.ts            # **APPLICATION CONSTANTS**
│   │                            # - ROUTES: auth, dashboard, projectDetail, etc.
│   │                            # - App configuration constants
│   │
│   └── utils.ts (if exists)    # General utility functions
│
├── types/                      # **SHARED TYPES**
│   ├── project.ts              # Project, ProjectInput types
│   ├── auth.ts (if separate)   # Auth types
│   └── index.ts                # Type exports
│
├── contexts/                   # **REACT CONTEXTS** (if used)
│   └── AuthProvider.tsx        # Auth state provider (optional)
│
├── middleware.ts               # Next.js middleware (optional)
│
├── .env.local                  # Environment variables (git-ignored)
├── .env.example                # Template for .env.local
│
├── next.config.ts              # Next.js configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.ts          # Tailwind CSS configuration (v4)
├── eslint.config.mjs           # ESLint rules
├── package.json                # Dependencies
├── package-lock.json           # Dependency lock file
└── README.md                   # Frontend README
```

### Key Frontend Patterns

**Server Components (async):**
```typescript
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const user = await getCurrentUser();  // server-side
  const projects = await listRecentProjects(5);  // server-side API call
  return <Dashboard user={user} projects={projects} />;
}
```

**Client Components (interactive):**
```typescript
// features/projects/components/CreateProjectButton.tsx
"use client";
export function CreateProjectButton() {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();
  // ... form logic, calls projectService.createProject()
}
```

**Form Validation (client + server):**
```typescript
// features/projects/utils/validation.ts
validateProjectForm(values) {
  // Client: name required, description length, dates order
  // Server: Pydantic validates on create/update
}
```

**Data Flow:**
1. Page component (server) fetches data using cookies
2. Passes data to client components
3. Client component (e.g., form) makes API call via `apiRequest<T>`
4. API call includes cookies (credentials: "include")
5. Backend validates and returns typed response

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────────┐
│        USERS            │
├─────────────────────────┤
│ id (PK, BIGINT)         │
│ full_name (NVARCHAR)    │
│ email (NVARCHAR, UQ)    │
│ password_hash           │
│ created_at (DATETIME2)  │
└──────────┬──────────────┘
           │
           ├──────────────────┬─────────────────────┬─────────────────┐
           │                  │                     │                 │
┌──────────▼──────────┐ ┌─────▼──────────────┐ ┌───▼──────────────┐ │
│  REFRESH_TOKENS     │ │PASSWORD_RESET_...  │ │   PROJECTS      │ │
├─────────────────────┤ ├────────────────────┤ ├─────────────────┤ │
│ id (PK)             │ │ id (PK)             │ │ id (PK)         │ │
│ user_id (FK → U)    │ │ user_id (FK → U)   │ │ owner_id (FK→U) │ │
│ token_hash          │ │ token_hash          │ │ name            │ │
│ expires_at          │ │ expires_at          │ │ description     │ │
│ created_at          │ │ created_at          │ │ start_date      │ │
└─────────────────────┘ └────────────────────┘ │ end_date        │ │
                                               │ created_at      │ │
                                               │ updated_at      │ │
                                               └─────────────────┘
```

### Table Details

#### `users`
| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | BIGINT | PK, Identity | Auto-increment |
| `full_name` | NVARCHAR(255) | NOT NULL | User's display name |
| `email` | NVARCHAR(255) | NOT NULL, UNIQUE | Sign-in identifier |
| `password_hash` | NVARCHAR(MAX) | NOT NULL | Argon2id hash |
| `created_at` | DATETIME2 | NOT NULL, default SYSUTCDATETIME() | UTC timestamp |

**Indexes:**
- PK on `id`
- UNIQUE on `email`
- Non-clustered on `created_at` (for sorting)

#### `refresh_tokens`
| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | BIGINT | PK, Identity | Auto-increment |
| `user_id` | BIGINT | NOT NULL, FK | Points to users(id) CASCADE |
| `token_hash` | NVARCHAR(MAX) | NOT NULL | SHA-256 of the token |
| `expires_at` | DATETIME2 | NOT NULL | When token expires (UTC) |
| `created_at` | DATETIME2 | NOT NULL | When issued (UTC) |

**Indexes:**
- PK on `id`
- Non-clustered on `user_id` (for lookup by user)

**Behavior:**
- Tokens rotate on refresh; old token is revoked
- Grace window: 10s (allows retry if network drops)
- Reuse outside grace window: all user sessions revoked

#### `password_reset_tokens`
| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | BIGINT | PK, Identity | Auto-increment |
| `user_id` | BIGINT | NOT NULL, FK | Points to users(id) CASCADE |
| `token_hash` | NVARCHAR(MAX) | NOT NULL | SHA-256 of the token |
| `expires_at` | DATETIME2 | NOT NULL | 24h expiry |
| `created_at` | DATETIME2 | NOT NULL | When created |

**Indexes:**
- PK on `id`
- Non-clustered on `(user_id, created_at)` (find latest per user)

**Behavior:**
- One-time use; revoked after password is set
- Expired tokens are cleaned up lazily

#### `projects`
| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | BIGINT | PK, Identity | Auto-increment |
| `owner_id` | BIGINT | NOT NULL, FK | Points to users(id) CASCADE |
| `name` | NVARCHAR(255) | NOT NULL | Project title |
| `description` | NVARCHAR(MAX) | NULL | Long text (up to 5,000 chars) |
| `start_date` | DATE | NULL | Project start (YYYY-MM-DD) |
| `end_date` | DATE | NULL | Project end (YYYY-MM-DD) |
| `created_at` | DATETIME2 | NOT NULL | When created (UTC) |
| `updated_at` | DATETIME2 | NOT NULL | Last modified (UTC) |

**Constraints:**
- PK on `id`
- FK on `owner_id` (CASCADE on delete)
- CHECK `ck_projects_end_after_start`: `end_date IS NULL OR start_date IS NULL OR end_date >= start_date`
- Non-clustered index on `(owner_id, created_at)` (for list queries)

**Behavior:**
- Projects are isolated by owner (access control)
- Dates are optional (can be added later)
- Timestamps always in UTC
- Updated_at changes on any edit

---

### Document and Chunk Tables (migrations 005 and 006)

Documents attached to a project flow down this chain: each source has at most one
extracted text, and each text is split into chunks. Chunks keep their start and end
offsets so any quote can be checked with `content_text[start_char:end_char]`.

```
┌───────────────────────────────────────────┐
│ CONTEXT_SOURCES                           │
├──────────────────────┬────────┬───────────┤
│ bigint               │ id     │ PK        │
│ bigint               │ project_id       │ FK → projects
│ bigint               │ created_by       │ FK → users
│ nvarchar_255         │ title            │
│ nvarchar_255         │ original_filename│
│ nvarchar_500         │ blob_path        │
│ nvarchar_100         │ mime_type        │
│ bigint               │ file_size_bytes  │
│ nvarchar_20          │ processing_status│ processing / ready / failed
│ nvarchar_500         │ failure_reason   │
│ datetime2            │ created_at       │
│ datetime2            │ deleted_at       │ soft delete
└───────────────────────────────────────────┘
                     │ 1
                     ▼ 0..1
┌───────────────────────────────────────────┐
│ CONTEXT_CONTENT                           │
├──────────────────────┬────────────────────┤
│ bigint               │ id               │ PK
│ bigint               │ context_source_id│ FK, UK → context_sources
│ nvarchar_max         │ content_text     │ extracted text
│ nvarchar_50          │ extraction_method│
│ datetime2            │ created_at       │
└───────────────────────────────────────────┘
                     │ 1
                     ▼ 0..n
┌───────────────────────────────────────────┐
│ CONTEXT_CHUNKS                            │
├──────────────────────┬────────────────────┤
│ bigint               │ id               │ PK
│ bigint               │ context_content_id│ FK → context_content, UK(content, number)
│ int                  │ chunk_number     │ starts at 1, document order
│ nvarchar_max         │ chunk_text       │ exactly content_text[start:end]
│ int                  │ start_char       │ 0-based offset of first character
│ int                  │ end_char         │ offset just after last character
│ int                  │ char_count       │ = end_char - start_char
│ int                  │ page_number      │ NULL when the extractor gives no page
│ datetime2            │ created_at       │
└───────────────────────────────────────────┘
```

#### `context_chunks`
| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | BIGINT | PK, Identity | Auto-increment |
| `context_content_id` | BIGINT | NOT NULL, FK | Points to context_content(id) CASCADE |
| `chunk_number` | INT | NOT NULL, CHECK >= 1 | Document order, starts at 1 |
| `chunk_text` | NVARCHAR(MAX) | NOT NULL | Exact slice of content_text |
| `start_char` | INT | NOT NULL, CHECK >= 0 | First character, 0-based |
| `end_char` | INT | NOT NULL, CHECK > start_char | Offset just after the last character |
| `char_count` | INT | NOT NULL, CHECK = end_char - start_char | Redundant on purpose, checked by the database |
| `page_number` | INT | NULL | From the last "Page N:" marker before start_char |
| `created_at` | DATETIME2 | NOT NULL, default SYSUTCDATETIME() | UTC timestamp |

**Constraints and indexes:**
- UNIQUE `(context_content_id, chunk_number)`: no duplicate numbering, and a second chunking call cannot insert twice
- Index on `context_content_id`
- Rows are never updated or deleted. A changed document gets a new content row and new chunks.

## How to Scale This Application

### Horizontal Scaling

**Frontend:**
- Deploy Next.js to a CDN (Vercel, Netlify, AWS CloudFront)
- Enable caching on static assets
- Use server-side rendering for SEO

**Backend:**
- Run multiple FastAPI instances behind a load balancer (Kubernetes, Docker Swarm)
- Each instance connects to the same Azure SQL database
- Scale based on request volume (CPU, memory)

### Database Scaling

**Current Setup:**
- Single Azure SQL instance (Discoveryhub)
- Good for <10k users
- Indexes on `(owner_id, created_at)` enable fast queries

**Future Scaling:**
- Azure SQL Read Replicas for analytics queries
- Partition projects table by `owner_id` if it grows very large
- Archive old projects to cold storage
- Implement caching layer (Redis) for frequently accessed projects

### Feature Scaling

**Add New Features:**
1. Create new migration (e.g., `005_add_collaborators.py`)
2. Update ORM model in `models.py`
3. Add schema in `schemas/`
4. Implement service in `services/`
5. Add routes in `api/routes/`
6. Add tests in `tests/`
7. Add frontend feature module in `features/`

**Example: Adding Collaborators**
```
Backend:
  - New table: project_collaborators (project_id, user_id, role, created_at)
  - New endpoints: POST /api/projects/{id}/collaborators, GET ...
  - Update project_service to list collaborators

Frontend:
  - New component: CollaboratorsList
  - New feature: features/collaborators/
  - Update overview page to show & manage collaborators
```

### Performance Optimization

**Backend:**
- Add query caching for frequently accessed data
- Batch database queries
- Implement pagination for large result sets
- Add query indexes as new filters are introduced

**Frontend:**
- Use Next.js partial pre-rendering for static pages
- Implement incremental static regeneration (ISR)
- Code-split by feature module
- Use React.lazy() for heavy components

**Database:**
- Monitor slow queries using Azure SQL insights
- Analyze execution plans
- Add indexes on WHERE/JOIN columns
- Archive or partition large tables

---

## Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for testing

# Copy and edit environment variables
copy .env.example .env
# Edit .env with real DATABASE_URL and JWT_SECRET_KEY

# Apply migrations
alembic upgrade head

# Run tests
python -m pytest -q

# Start server
uvicorn app.main:app --reload --port 8000
```

**Test Coverage:**
- `test_projects.py`: 12 tests covering CRUD, isolation, validation, auth

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
copy .env.example .env.local
# Edit .env.local with NEXT_PUBLIC_API_URL

# Start dev server (with hot reload)
npm run dev
# Open http://localhost:3001

# Type checking
npx tsc --noEmit

# Linting
npx eslint .

# Build for production
npm run build
npm run start
```

**Browser Testing:**
- E2E test: `scratchpad/e2e-projects/projects_flow.mjs` (Playwright)
- Covers: sign-up → create → overview → edit → list → isolation

---

## Key Concepts & Terminology

### Authentication
- **Access Token**: Short-lived JWT (15m) sent as HttpOnly cookie
- **Refresh Token**: Long-lived token (30d) used to rotate access token
- **Session**: pair of access + refresh tokens for a signed-in user

### Authorization
- **Owner**: User who created the resource (project)
- **Access Control**: Only owner can view/edit their projects
- **Status Codes**:
  - `404 PROJECT_NOT_FOUND`: Missing OR foreign project (no 403)
  - `401 UNAUTHENTICATED`: Missing/invalid access token

### Projects
- **Metadata**: name (required), description (optional), dates (optional)
- **Ownership**: Projects belong to a user; isolation enforced in queries
- **Timestamps**: `created_at` (immutable), `updated_at` (changes on edit)
- **Date Order**: Validated (end_date >= start_date) on create and update

### API Patterns
- **Error Format**: `{"detail": {"code": "ERROR_CODE", "message": "..."}}`
- **Pagination**: `limit` query param (1–50, default 5)
- **Ordering**: Most recently updated first (updated_at DESC, id DESC)

---

## Common Tasks

### Add a New Project Field

1. **Backend (models.py):**
   ```python
   class Project(Base):
       ...
       category: Mapped[str | None] = mapped_column(String(50))
   ```

2. **Create migration:**
   ```bash
   alembic revision --autogenerate -m "add_project_category"
   alembic upgrade head
   ```

3. **Update schemas:**
   ```python
   class ProjectCreate(BaseModel):
       ...
       category: str | None = None
   ```

4. **Update frontend (ProjectFormValues):**
   ```typescript
   export type ProjectFormValues = {
     ...
     category: string;
   }
   ```

### Add a New Endpoint

1. Create route in `api/routes/projects.py` (or new file)
2. Use `get_current_user` dependency
3. Call appropriate `project_service` function
4. Return typed response (Pydantic schema)
5. Add tests in `tests/test_projects.py`

### Deploy to Production

**Backend:**
1. Build Docker image (include requirements.txt)
2. Deploy to container registry (Azure Container Registry)
3. Run as App Service or AKS pod
4. Set environment variables (DATABASE_URL, JWT_SECRET_KEY)
5. Run `alembic upgrade head` on startup

**Frontend:**
1. Set `NEXT_PUBLIC_API_URL` to production backend
2. Build: `npm run build`
3. Deploy to CDN (Vercel, Netlify, AWS)
4. Test all auth flows and project CRUD

---

## References

- **Backend README:** `backend/README.md`
- **Auth System Docs:** `Creation-of-Auth-System.md`
- **Design System:** `frontend/docs/design-system.md`, `.claude/skills/ui-design-system/SKILL.md`
- **Frontend Agents:** `frontend/AGENTS.md`
- **Live API Docs:** http://localhost:8000/docs (interactive Swagger UI)

---

## Questions?

For architectural decisions, design patterns, or feature implementation questions:
1. Check the relevant `README.md` in backend/ or frontend/
2. Review existing test cases for usage examples
3. Consult the design-system documentation
4. Search git log for similar implementations

**Key Contacts:**
- Backend logic: `backend/app/services/` (business rules)
- Frontend state: `frontend/features/*/services/` (data fetching & validation)
- Database: `backend/alembic/versions/` (schema history)

---

**Last Updated:** 2026-11-11
**Version:** 1.0 (Project Creation MVP)
