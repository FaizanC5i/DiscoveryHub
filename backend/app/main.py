"""
Application entry point: builds the FastAPI app and wires in middleware, routes and error handlers.

Run from the backend/ folder:
    uvicorn app.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routes.auth import register_auth_error_handler, router as auth_router
from app.core.config import get_settings
from app.core.rate_limit import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)

settings = get_settings()

app = FastAPI(title="DiscoveryHub API")

# --- CORS ------------------------------------------------------------------
# Lets the Next.js app (a different origin, http://localhost:3000) call this API.
# allow_credentials=True is required so the browser sends and accepts cookies.
# Origins must be explicit when credentials are allowed: "*" is not permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# --- Rate limiting ------------------------------------------------------------
app.state.limiter = limiter


async def _rate_limited(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Same JSON shape as the other auth errors, so the frontend handles it the same way.
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "code": "RATE_LIMITED",
                "message": "Too many attempts. Please wait a minute and try again.",
            }
        },
    )


app.add_exception_handler(RateLimitExceeded, _rate_limited)

# --- Auth error shape -----------------------------------------------------------
register_auth_error_handler(app)

# --- Routes -----------------------------------------------------------------------
app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
