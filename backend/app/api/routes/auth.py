"""
HTTP endpoints for authentication, mounted under /api/auth.

Analogy: the front desk. It takes the guest's request, calls the back office
(services/auth_service.py) for the decision, and then hands over the key cards
(cookies) and a receipt (JSON). It contains no policy of its own, so the rules
are never duplicated.

Errors raised by the service layer (AuthError) are turned into JSON responses by
the handler registered in main.py.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import REFRESH_COOKIE, clear_session_cookies, set_session_cookies
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignUpRequest,
    UserResponse,
)
from app.services import auth_service
from app.services.auth_service import AuthError
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("app.auth.routes")

DbSession = Annotated[Session, Depends(get_db)]

# Same answer for every forgot-password request, known or unknown email.
FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, a password reset link has been sent."
)


def _user_out(user) -> UserResponse:
    return UserResponse(id=user.id, name=user.name, email=user.email)


@router.post("/signup", status_code=201, response_model=UserResponse)
def sign_up(payload: SignUpRequest, response: Response, db: DbSession) -> UserResponse:
    """Create an account and sign the new user in straight away."""
    user = auth_service.sign_up(db, payload.name, payload.email, payload.password)
    session = auth_service.issue_session(db, user)
    set_session_cookies(response, session.access_token, session.refresh_token)
    return _user_out(user)


@router.post("/login", response_model=UserResponse)
@limiter.limit(lambda: get_settings().login_rate_limit)
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: DbSession,
) -> UserResponse:
    """Check credentials and start a session. Sets both cookies on success."""
    user = auth_service.authenticate(db, payload.email, payload.password)
    session = auth_service.issue_session(db, user)
    set_session_cookies(response, session.access_token, session.refresh_token)
    return _user_out(user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: DbSession) -> MessageResponse:
    """
    Cancel this device's session and clear the cookies.

    Works even with an expired access token: logout only needs the refresh cookie.
    """
    auth_service.revoke_refresh_token(db, request.cookies.get(REFRESH_COOKIE))
    clear_session_cookies(response)
    return MessageResponse(message="Signed out")


@router.post("/refresh", response_model=UserResponse)
def refresh(request: Request, response: Response, db: DbSession) -> UserResponse | JSONResponse:
    """
    Trade the refresh cookie for a fresh access token and a fresh refresh token.

    Called by the frontend when an access token has expired (401), and by the
    Next.js proxy before serving a page with an expired session.

    Failure path: we return the error response ourselves, not by raising. An
    exception would discard the injected `response`, and the cookie-clearing
    headers we attach to a dead session would be lost.
    """
    raw = request.cookies.get(REFRESH_COOKIE)
    try:
        if not raw:
            raise AuthError(401, "INVALID_REFRESH", "Please sign in")
        session = auth_service.refresh_session(db, raw)
    except AuthError as exc:
        failure = auth_error_response(exc)
        clear_session_cookies(failure)
        return failure

    set_session_cookies(response, session.access_token, session.refresh_token)
    return _user_out(session.user)


def auth_error_response(exc: AuthError) -> JSONResponse:
    """The one JSON shape every auth error uses: {"detail": {"code", "message"}}."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


def register_auth_error_handler(app: FastAPI) -> None:
    """Make any AuthError raised in a route or service become the JSON above."""

    @app.exception_handler(AuthError)
    async def _handle(_request: Request, exc: AuthError) -> JSONResponse:
        return auth_error_response(exc)


def _send_reset_email_safely(to_address: str, reset_link: str) -> None:
    """
    Runs in the background after the response is sent.

    Any failure is logged, not raised. Nobody is waiting for this task, and an
    error message here would reveal to the caller whether the account exists.
    """
    try:
        send_password_reset_email(to_address, reset_link)
    except Exception:  # noqa: BLE001 - deliberately broad: background task must never crash silently
        logger.exception("password_reset_email_failed")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(lambda: get_settings().forgot_password_rate_limit)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> MessageResponse:
    """
    Start a password reset. Always returns the same message.

    The email is sent in the background, so the response is the same whether or
    not an account exists.
    """
    raw = auth_service.request_password_reset(db, payload.email)
    if raw is not None:
        settings = get_settings()
        link = f"{settings.frontend_url}/reset-password?token={raw}"
        background_tasks.add_task(_send_reset_email_safely, payload.email, link)
    return MessageResponse(message=FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    """Spend a reset token and set a new password. Ends all existing sessions."""
    auth_service.reset_password(db, payload.token, payload.password)
    return MessageResponse(message="Your password has been reset. You can now sign in.")


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    """Return the signed-in user. 401 if the access token is missing, expired or invalid."""
    return _user_out(user)
