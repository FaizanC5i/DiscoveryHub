"""
Database verification: proves the three auth tables work together against Azure SQL.

What it does, in order:
  1. Inserts a test user.
  2. Inserts a refresh token (a "session") linked to that user.
  3. Inserts a password reset token linked to that user.
  4. Reads all three back through their foreign keys and checks the links.
  5. Deletes everything it created, then confirms nothing is left.

Analogy: a fire drill. You do not wait for a real fire to find out the alarm
is broken. The drill uses a dummy guest, runs every exit, and leaves the
building as it found it.

Run from backend/:
    python scripts/verify_db.py

Exit code 0 means every step passed. Anything else means the schema or the
database connection needs attention.
"""

import sys
import uuid
from pathlib import Path

# Make "app" importable when this file is run directly from backend/scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402

from app.core.security import generate_opaque_token, hash_password, hash_token  # noqa: E402
from app.core.time import add_days, add_minutes, utc_now  # noqa: E402
from app.db.models import PasswordResetToken, RefreshToken, User  # noqa: E402
from app.db.session import get_session_factory  # noqa: E402


def step(message: str) -> None:
    print(f"  [ ] {message}")


def ok(message: str) -> None:
    print(f"  [x] {message}")


def main() -> int:
    session_factory = get_session_factory()
    test_email = f"verify-{uuid.uuid4().hex[:12]}@example.invalid"
    now = utc_now()
    created_user_id: int | None = None

    print("Database verification")

    try:
        # 1-3. Insert the user, a session and a reset token, then COMMIT so the rows
        # really persist. Committing (not just flushing) is what proves the schema works.
        with session_factory() as db:
            step("Insert a test user, a refresh token (session) and a reset token")
            user = User(
                name="Verify Script",
                email=test_email,
                password_hash=hash_password("verify-only-Password1"),
                is_active=True,
            )
            db.add(user)
            db.flush()  # gives us the identity id before the commit
            created_user_id = user.id

            raw_refresh = generate_opaque_token()
            raw_reset = generate_opaque_token()
            db.add(
                RefreshToken(
                    user_id=user.id,
                    token_hash=hash_token(raw_refresh),
                    expires_at=add_days(now, 30),
                )
            )
            db.add(
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=hash_token(raw_reset),
                    expires_at=add_minutes(now, 30),
                )
            )
            db.commit()
            ok(f"committed: user id={user.id}, 1 session, 1 reset token (hashes only)")

        # 4. Read back in a NEW session, so we see what the database stored, not our cache.
        with session_factory() as db:
            step("Read back through the foreign keys in a fresh session")
            loaded = db.scalar(select(User).where(User.id == created_user_id))
            if loaded is None:
                raise RuntimeError("user row not found after commit")
            if len(loaded.refresh_tokens) != 1:
                raise RuntimeError(f"expected 1 refresh token, found {len(loaded.refresh_tokens)}")
            if len(loaded.password_reset_tokens) != 1:
                raise RuntimeError(
                    f"expected 1 reset token, found {len(loaded.password_reset_tokens)}"
                )
            if loaded.refresh_tokens[0].token_hash != hash_token(raw_refresh):
                raise RuntimeError("stored refresh token hash does not match")
            if loaded.password_reset_tokens[0].token_hash != hash_token(raw_reset):
                raise RuntimeError("stored reset token hash does not match")
            if loaded.refresh_tokens[0].token_hash == raw_refresh:
                raise RuntimeError("raw refresh token was stored in plain text")
            ok("foreign keys link correctly; stored values are hashes, not raw tokens")

    finally:
        # 5. Clean up in its own session, even if a check above failed.
        with session_factory() as db:
            step("Delete the test rows (children first, then the user)")
            db.execute(
                delete(PasswordResetToken).where(PasswordResetToken.user_id == created_user_id)
            )
            db.execute(delete(RefreshToken).where(RefreshToken.user_id == created_user_id))
            db.execute(delete(User).where(User.email == test_email))
            db.commit()
            ok("cleanup committed")

    # Confirm the cleanup really removed everything.
    with session_factory() as db:
        remaining = db.scalar(select(User.id).where(User.email == test_email))
        if remaining is not None:
            print("  [!] cleanup incomplete: test user still present")
            return 1

    print("\nAll checks passed. Tables users, refresh_tokens and password_reset_tokens work with their foreign keys.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - print a clean message for the operator
        print(f"\nVerification FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)
