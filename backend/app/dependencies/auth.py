"""
FastAPI dependency that identifies the caller from the access cookie.

Analogy: the door security at a venue. A route that declares
`user: CurrentUser` is a door that opens only for a valid wristband. The door
checks the wristband (signature and expiry) and then the guest list (the user
still exists and is active). Route code runs only after both checks pass.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.cookies import ACCESS_COOKIE
from app.core.security import InvalidAccessToken, decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.services.auth_service import get_user_by_id


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise _unauthorized()

    try:
        user_id = decode_access_token(token)
    except InvalidAccessToken:
        raise _unauthorized() from None

    # Re-check the database on every request. The signature proves the token was
    # issued, not that the account is still active. Without this lookup, a
    # disabled user keeps access until their 15-minute token expires.
    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


def _unauthorized() -> HTTPException:
    # Same message for every failure, so an attacker learns nothing from the reason.
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHENTICATED", "message": "Please sign in"},
    )


CurrentUser = Annotated[User, Depends(get_current_user)]
