"""Public URLs and cookie policy. These values are configuration, not secrets."""

import os
from urllib.parse import urlsplit

HTTPS = os.getenv("LEARNLOOP_HTTPS", "0") == "1"
APP_ORIGIN = os.getenv("LEARNLOOP_APP_ORIGIN", "http://localhost:3000").rstrip("/")
BACKEND_ORIGIN = os.getenv("LEARNLOOP_BACKEND_ORIGIN", "http://localhost:8000").rstrip("/")
SESSION_SECONDS = 8 * 60 * 60
COOKIE_NAME = "__Host-learnloop_session" if HTTPS else "learnloop_session"

for origin in (APP_ORIGIN, BACKEND_ORIGIN):
    url = urlsplit(origin)
    if url.scheme not in ("http", "https") or not url.netloc or url.path or url.query or url.fragment or url.username:
        raise ValueError("LearnLoop origins must be complete http(s) origins without paths or credentials.")
    if HTTPS and url.scheme != "https":
        raise ValueError("LEARNLOOP_HTTPS=1 requires HTTPS for both public origins.")
    if not HTTPS and url.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("HTTP development is limited to loopback. Use HTTPS for other hosts.")
if urlsplit(APP_ORIGIN).hostname != urlsplit(BACKEND_ORIGIN).hostname:
    raise ValueError("The frontend and backend must share a hostname for the host-only session cookie.")
