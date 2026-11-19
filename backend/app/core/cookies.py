"""
Session cookies: where the access and refresh tokens are kept in the browser.

Analogy: the tokens are sealed envelopes the server hands the browser. The
browser carries them on every request, but JavaScript on the page cannot open
them. HttpOnly is the "do not open" stamp; Secure says "only deliver over HTTPS";
SameSite says "only send along when the request starts from our own site".

Why cookies and not localStorage? Anything JavaScript can read, a cross-site
script injection (XSS) can also read and send to an attacker. HttpOnly cookies
remove that path entirely.
"""

from fastapi import Response

from app.core.config import get_settings

# Shared with the Next.js proxy and server components, which read these exact names.
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

# Path "/" so the browser sends the refresh cookie to the Next.js server too.
# The Next.js proxy needs it to refresh a session during page navigation.
COOKIE_PATH = "/"


def set_session_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Attach both tokens to the outgoing response with their lifetimes."""
    settings = get_settings()
    common = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": settings.cookie_samesite,
        "path": COOKIE_PATH,
    }
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.access_token_minutes * 60,
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        **common,
    )


def clear_session_cookies(response: Response) -> None:
    """
    Expire both cookies in the browser.

    The attributes must match the ones used when setting, or the browser keeps
    the old cookie. Clearing sets max_age=0, which tells the browser to delete now.
    """
    settings = get_settings()
    common = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": settings.cookie_samesite,
        "path": COOKIE_PATH,
    }
    response.delete_cookie(ACCESS_COOKIE, **common)
    response.delete_cookie(REFRESH_COOKIE, **common)
