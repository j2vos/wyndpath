"""WyndPath — official Python client.

WyndPath is a Europe-hosted web scraping / anti-bot API. You send a URL, WyndPath
picks the right path (light HTTP or a real browser engine), gets past protections
like Cloudflare and DataDome, and returns the response. JSON endpoints are returned
as JSON. You are billed only on success.

    from wyndpath import WyndPath

    wp = WyndPath("wk_your_key")
    data = wp.get_json("https://www.vinted.fr/api/v2/catalog/items?search_text=nike")
    print(len(data["items"]))

Docs: https://console.wyndpath.com/docs  ·  Console: https://console.wyndpath.com
"""
from __future__ import annotations

import os
from typing import Any

import requests

__version__ = "1.0.0"
__all__ = [
    "WyndPath", "Response",
    "WyndPathError", "InvalidApiKey", "QuotaExceeded", "LoginRequired",
    "TooManyConcurrent", "TargetBlocked",
]

DEFAULT_BASE_URL = "https://api.wyndpath.com/v1/"


class WyndPathError(Exception):
    """Base error. Carries the HTTP status, the WyndPath error code and the payload."""

    def __init__(self, code: str, status: int, payload: dict | None = None):
        self.code = code
        self.status = status
        self.payload = payload or {}
        super().__init__(f"[{status}] {code}: {self.payload}")


class InvalidApiKey(WyndPathError):
    """401 — the API key is missing or invalid."""


class QuotaExceeded(WyndPathError):
    """402 — the monthly credit quota is reached. See .payload['limit'] / ['used']."""


class LoginRequired(WyndPathError):
    """428 — the target needs credentials you have not provided yet.

    Provide them once in your console (Targets), then retry. See .payload['needs'].
    """


class TooManyConcurrent(WyndPathError):
    """429 — too many concurrent requests for your plan (or for a logged-in target)."""


class TargetBlocked(WyndPathError):
    """502 — the target could not be fetched yet. WyndPath will study it automatically
    (nightly onboarding); retry later. See .payload.get('study')."""


_ERRORS = {
    401: InvalidApiKey,
    402: QuotaExceeded,
    428: LoginRequired,
    429: TooManyConcurrent,
    502: TargetBlocked,
}


class Response:
    """A WyndPath fetch result.

    Attributes:
        text (str):   raw response body.
        status (int): the TARGET's final HTTP status (X-WyndPath-Final-Status).
        credits (int):credits billed for this call (0 if it failed).
        engine (str): engine used (light / flaresolverr / nodriver / trawl).
        route (str):  'light' or 'browser'.
        headers (dict): the HTTP response headers from WyndPath.
    """

    def __init__(self, resp: requests.Response):
        self._resp = resp
        self.text = resp.text
        self.headers = resp.headers
        self.status = _int(resp.headers.get("X-WyndPath-Final-Status"))
        self.credits = _int(resp.headers.get("X-WyndPath-Credits")) or 0
        self.engine = resp.headers.get("X-WyndPath-Engine")
        self.route = resp.headers.get("X-WyndPath-Route")

    def json(self, **kwargs) -> Any:
        """Parse the body as JSON (works out of the box for API endpoints)."""
        return self._resp.json(**kwargs)

    @property
    def content(self) -> bytes:
        return self._resp.content

    def __repr__(self) -> str:
        return f"<wyndpath.Response status={self.status} engine={self.engine} credits={self.credits}>"


class WyndPath:
    """WyndPath API client.

    Args:
        api_key: your key (``wk_...``). Falls back to the WYNDPATH_API_KEY env var.
        base_url: override the API base URL (default: production).
        timeout: per-request timeout in seconds (default 120).
    """

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL, timeout: int = 120):
        self.api_key = api_key or os.environ.get("WYNDPATH_API_KEY", "")
        if not self.api_key:
            raise InvalidApiKey("missing_api_key", 401, {"hint": "pass api_key or set WYNDPATH_API_KEY"})
        self.base_url = base_url
        self.timeout = timeout
        self._session = requests.Session()

    def fetch(
        self,
        url: str,
        *,
        render_js: bool = False,
        country: str | None = None,
        session: str | None = None,
        method: str = "GET",
        data: Any = None,
        **params: Any,
    ) -> Response:
        """Fetch ``url`` through WyndPath and return a :class:`Response`.

        Args:
            url: the target URL to fetch.
            render_js: run a real browser (needed for JS-heavy / hard anti-bot sites).
            country: exit country, e.g. ``"fr"``.
            session: a stable value to chain several calls from the same IP.
            method: HTTP method for the target (GET/POST).
            data: request body for non-GET methods.
            **params: any other WyndPath parameter (e.g. optimize_request=1, max_cost=10).

        Raises:
            LoginRequired, QuotaExceeded, TooManyConcurrent, TargetBlocked, WyndPathError.
        """
        q: dict[str, Any] = {"api_key": self.api_key, "url": url}
        if render_js:
            q["render_js"] = 1
        if country:
            q["country"] = country
        if session:
            q["session"] = session
        q.update(params)

        resp = self._session.request(
            method.upper() if data is not None else "GET",
            self.base_url, params=q, data=data, timeout=self.timeout,
        )
        self._raise_for_error(resp)
        return Response(resp)

    def get_json(self, url: str, **kwargs) -> Any:
        """Convenience: :meth:`fetch` then parse the body as JSON."""
        return self.fetch(url, **kwargs).json()

    def _raise_for_error(self, resp: requests.Response) -> None:
        # A WyndPath-level error is a JSON body ``{"error": "code", ...}``.
        ctype = resp.headers.get("content-type", "")
        if resp.status_code >= 400 and "application/json" in ctype:
            try:
                payload = resp.json()
            except ValueError:
                payload = {}
            code = payload.get("error", "error")
            exc = _ERRORS.get(resp.status_code, WyndPathError)
            raise exc(code, resp.status_code, payload)


def _int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
