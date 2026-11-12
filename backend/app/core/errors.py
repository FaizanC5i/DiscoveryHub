"""Shared helper so every error uses the same {"detail": {"code", "message"}} shape."""

from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})