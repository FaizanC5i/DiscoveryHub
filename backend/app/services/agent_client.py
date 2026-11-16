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


def _post(payload: dict, agent_name_field: str, prefix: str) -> dict:
    settings = get_settings()
    if not (settings.agent5i_webhook_url and settings.agent5i_username and settings.agent5i_password):
        raise AgentConfigurationError("Agent5i is not configured. Set the AGENT5I_* variables in backend/.env.")
    agent_name = getattr(settings, agent_name_field)

    text_input = prefix + json.dumps(payload, ensure_ascii=False)
    body = {
        "username": settings.agent5i_username,
        "password": settings.agent5i_password,
        "name": agent_name,
        settings.agent5i_source_input_name: text_input,
    }
    request = Request(
        settings.agent5i_webhook_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    timeout_message = f"Agent5i did not answer within {settings.agent5i_timeout_seconds} seconds."
    try:
        with urlopen(request, timeout=settings.agent5i_timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        # HTTPError is a subclass of URLError, so it must be caught first.
        raise AgentHttpError(exc.code) from None
    except (TimeoutError, socket.timeout):
        raise AgentTimeoutError(timeout_message) from None
    except URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            raise AgentTimeoutError(timeout_message) from None
        raise AgentConnectionError("Agent5i could not be reached.") from None

    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        raise AgentInvalidResponseError("Agent5i returned a body that is not JSON.") from None
