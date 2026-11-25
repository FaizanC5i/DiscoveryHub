"""
Sends requests to the Agent5i webhook. One function posts, and each agent is a thin wrapper.

Analogy: a courier. We seal the parcel with our account details, post it, and wait for the
reply. If the courier does not answer in time we say so; we never guess the reply. The
retry policy decides whether to send the parcel again, based on the error type.

Security: the credentials come from settings (environment variables) and travel only in the
request body to the configured webhook. They are never logged, and error messages carry the
HTTP status or a fixed sentence, never the request body.
"""

import json
import logging
import socket
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings

log = logging.getLogger(__name__)

HELPER_REQUEST_PREFIX = "CHECKPOINT_MAPPING_REQUEST\n"
MAX_ATTEMPTS = 3
RETRY_WAITS_SECONDS = (2, 4)

T = TypeVar("T")


class AgentError(Exception):
    """Base error for every failed call. `retryable` tells the caller whether another attempt can help."""

    retryable = False


class AgentConfigurationError(AgentError):
    """A required setting is missing. Retrying cannot fix it."""


class AgentHttpError(AgentError):
    """The webhook answered with an error status. Only 5xx is worth retrying."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"Agent5i returned HTTP {status_code}.")
        self.status_code = status_code
        self.retryable = status_code >= 500


class AgentTimeoutError(AgentError):
    """No answer within AGENT5I_TIMEOUT_SECONDS."""

    retryable = True


class AgentConnectionError(AgentError):
    """The webhook could not be reached at all."""


class AgentInvalidResponseError(AgentError):
    """The webhook answered, but the body was not JSON."""


def call_helper_agent(payload: dict) -> dict:
    """Checkpoint mapping: one batch of chunks against every active checkpoint."""
    return _post(payload, "agent5i_agent_name", HELPER_REQUEST_PREFIX)


BRD_INPUT_DIR = Path(__file__).resolve().parents[2] / "logs" / "brd_agent_inputs"
BRD_REPLY_DIR = Path(__file__).resolve().parents[2] / "logs" / "brd_agent_replies"


def _save_brd_input(text_input: str) -> None:
    """Write the exact text sent to the BRD agent to a markdown file, so the payload can be read later."""
    try:
        BRD_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = BRD_INPUT_DIR / f"{stamp}.md"
        path.write_text(
            f"# BRD agent input\n\nSent: {datetime.now().isoformat(timespec='seconds')}\n\n"
            f"```text\n{text_input}\n```\n",
            encoding="utf-8",
        )
        log.info("BRD agent input saved to %s", path)
    except OSError:
        log.exception("Could not save the BRD agent input")


def call_brd_agent(text_input: str) -> dict:
    """
    BRD generation. The BRD agent reads one text input: the AGENT_REQUEST control block followed
    by the approved checkpoint answers (built by brd_service), so the text is sent as it is.
    """
    _save_brd_input(text_input)
    settings = get_settings()
    reply = _post_text(
        text_input,
        agent_name=settings.brd_agent_name,
        username=settings.brd_agent5i_username or settings.agent5i_username,
        password=settings.brd_agent5i_password or settings.agent5i_password,
        timeout_seconds=settings.brd_timeout_seconds,
    )
    _save_brd_reply(reply)
    return reply


def _save_brd_reply(reply: dict) -> None:
    """Write the whole BRD agent reply to a file, so the complete response can be read later."""
    try:
        BRD_REPLY_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = BRD_REPLY_DIR / f"{stamp}.json"
        path.write_text(json.dumps(reply, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("BRD agent reply saved to %s", path)
    except OSError:
        log.exception("Could not save the BRD agent reply")


PRD_REQUEST_PREFIX = "PRD_REQUEST\n"
PRD_INPUT_DIR = Path(__file__).resolve().parents[2] / "logs" / "prd_agent_inputs"
PRD_REPLY_DIR = Path(__file__).resolve().parents[2] / "logs" / "prd_agent_replies"


def call_prd_agent(payload: dict) -> dict:
    """
    PRD generation. The PRD Generation Agent reads one text input: "PRD_REQUEST", a new line, then
    the request as JSON (built by prd_agent_io.build_payload). Input and reply are saved under logs/.
    """
    text_input = PRD_REQUEST_PREFIX + json.dumps(payload, ensure_ascii=False)
    _save_log(PRD_INPUT_DIR, "json", text_input[len(PRD_REQUEST_PREFIX):])
    settings = get_settings()
    reply = _post_text(
        text_input,
        agent_name=settings.prd_agent_name,
        username=settings.prd_agent5i_username or settings.agent5i_username,
        password=settings.prd_agent5i_password or settings.agent5i_password,
        timeout_seconds=settings.prd_timeout_seconds,
    )
    _save_log(PRD_REPLY_DIR, "json", json.dumps(reply, indent=2, ensure_ascii=False))
    return reply


def _save_log(folder: Path, extension: str, text: str) -> None:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{extension}"
        path.write_text(text, encoding="utf-8")
        log.info("Agent log saved to %s", path)
    except OSError:
        log.exception("Could not save the agent log in %s", folder)


def call_mom_agent(payload: dict) -> dict:
    """Meeting minutes: the payload is sent as JSON text in source_files, as the agent expects."""
    settings = get_settings()
    return _post_text(
        json.dumps(payload, ensure_ascii=False),
        agent_name=settings.mom_agent_name,
        username=settings.agent5i_username,
        password=settings.agent5i_password,
        timeout_seconds=settings.mom_timeout_seconds,
    )


def call_with_retry(call: Callable[[], T], description: str) -> T:
    """
    Up to MAX_ATTEMPTS attempts. Only timeouts and 5xx are retried, with waits of 2s, then 4s.

    Correctness: a configuration or 4xx error is raised at once, because sending the same
    request again cannot change the outcome.
    """
    attempt = 1
    while True:
        try:
            return call()
        except AgentError as exc:
            if not exc.retryable or attempt >= MAX_ATTEMPTS:
                raise
            wait = RETRY_WAITS_SECONDS[attempt - 1]
            log.warning("%s attempt %d failed (%s); retrying in %ds", description, attempt, exc, wait)
            time.sleep(wait)
            attempt += 1


NOT_CONFIGURED = "Agent5i is not configured. Set the AGENT5I_* variables in backend/.env."


def _post(payload: dict, agent_name_field: str, prefix: str) -> dict:
    settings = get_settings()
    # Checked before any other setting is read, so a missing login is always a configuration error.
    if not (settings.agent5i_webhook_url and settings.agent5i_username and settings.agent5i_password):
        raise AgentConfigurationError(NOT_CONFIGURED)
    return _post_text(
        prefix + json.dumps(payload, ensure_ascii=False),
        agent_name=getattr(settings, agent_name_field),
        username=settings.agent5i_username,
        password=settings.agent5i_password,
        timeout_seconds=settings.agent5i_timeout_seconds,
    )


def _post_text(text_input: str, agent_name: str, username: str, password: str, timeout_seconds: int) -> dict:
    settings = get_settings()
    if not (settings.agent5i_webhook_url and username and password):
        raise AgentConfigurationError(NOT_CONFIGURED)

    body = {
        "username": username,
        "password": password,
        "name": agent_name,
        settings.agent5i_source_input_name: text_input,
    }
    request = Request(
        settings.agent5i_webhook_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    timeout_message = f"Agent5i did not answer within {timeout_seconds} seconds."
    log.info("Agent5i request -> %s (%d characters, timeout %ds)", agent_name, len(text_input), timeout_seconds)
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        # HTTPError is a subclass of URLError, so it must be caught first.
        log.warning("Agent5i error <- %s: HTTP %d after %.1fs", agent_name, exc.code, time.monotonic() - started)
        raise AgentHttpError(exc.code) from None
    except (TimeoutError, socket.timeout):
        log.warning("Agent5i timeout <- %s after %.1fs", agent_name, time.monotonic() - started)
        raise AgentTimeoutError(timeout_message) from None
    except URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            log.warning("Agent5i timeout <- %s after %.1fs", agent_name, time.monotonic() - started)
            raise AgentTimeoutError(timeout_message) from None
        log.warning("Agent5i unreachable <- %s: %s", agent_name, type(exc.reason).__name__)
        raise AgentConnectionError("Agent5i could not be reached.") from None

    log.info("Agent5i reply <- %s in %.1fs (%d bytes)", agent_name, time.monotonic() - started, len(raw))
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        log.warning("Agent5i reply from %s is not JSON", agent_name)
        raise AgentInvalidResponseError("Agent5i returned a body that is not JSON.") from None
