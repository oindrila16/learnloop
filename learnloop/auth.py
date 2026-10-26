"""Password hashing and HTTP cookie sessions. Credentials never enter Reflex state."""

import re
import secrets
import time
from http.cookies import CookieError, SimpleCookie
from urllib.parse import parse_qs
from uuid import uuid4

from pwdlib import PasswordHash
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.routing import Route

from . import database as db
from .settings import APP_ORIGIN, COOKIE_NAME, HTTPS, SESSION_SECONDS

passwords = PasswordHash.recommended()
# Missing users still run the same expensive password verification.
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))
USERNAME = re.compile(r"[a-z0-9_]{3,30}\Z")
LOGIN_ERROR = "Username or password is incorrect, or login is temporarily unavailable. Please try again later."


def cookie_token(header: str) -> str:
    cookie = SimpleCookie()
    try:
        cookie.load(header)
    except CookieError:
        return ""
    return cookie[COOKIE_NAME].value if COOKIE_NAME in cookie else ""


def normalize_username(username: str) -> str:
    return username.strip().lower()


def register(username: str, password: str) -> str:
    username = normalize_username(username)
    if not USERNAME.fullmatch(username) or not 15 <= len(password) <= 128:
        raise ValueError("Check the username and password requirements.")
    # Hash before opening a database session. pwdlib uses Argon2id with a random salt.
    hashed = passwords.hash(password)
    user_id = str(uuid4())
    with Session(db.engine) as session:
        session.add(db.Learner(id=user_id, username=username, password_hash=hashed))
        session.commit()  # The unique username index also protects concurrent requests.
    return user_id


def authenticate(username: str, password: str) -> str | None:
    username = normalize_username(username)
    with Session(db.engine) as session:
        user = session.exec(select(db.Learner).where(db.Learner.username == username)).first()
        hashed = user.password_hash if user else DUMMY_HASH
        user_id = user.id if user else None
    if len(password) > 128:
        return None
    valid, updated_hash = passwords.verify_and_update(password, hashed)
    if not valid or user_id is None:
        return None
    if updated_hash:
        with Session(db.engine) as session:
            user = session.get(db.Learner, user_id)
            if user:
                user.password_hash = updated_hash
                session.add(user)
                session.commit()
    return user_id


def issue_session(user_id: str, previous_token: str = "") -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    with Session(db.engine) as session:
        with session.begin():
            session.exec(delete(db.LoginSession).where(db.LoginSession.expires_at <= now))
            if previous_token:
                session.exec(delete(db.LoginSession).where(db.LoginSession.token_hash == db.token_digest(previous_token)))
            session.add(db.LoginSession(token_hash=db.token_digest(token), user_id=user_id, expires_at=now + SESSION_SECONDS))
    return token


def revoke_session(token: str) -> None:
    if not token:
        return
    with Session(db.engine) as session:
        session.exec(delete(db.LoginSession).where(db.LoginSession.token_hash == db.token_digest(token)))
        session.commit()


def allow_auth_request(ip: str, username: str, registration: bool = False) -> bool:
    """Persistent, atomic quotas. Never trust a client-supplied forwarded IP."""
    now = int(time.time())
    window = now // 900 * 900
    limits = [(f"register:ip:{ip}", 10)] if registration else [
        (f"login:ip:{ip}", 30), (f"login:user:{normalize_username(username)}", 5),
    ]
    allowed = True
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM loginbucket WHERE window_start < :old"), {"old": window - 900})
        for key, limit in limits:
            result = connection.execute(text('''
                INSERT INTO loginbucket (key, window_start, count) VALUES (:key, :window, 1)
                ON CONFLICT(key) DO UPDATE SET
                    count = CASE WHEN window_start = :window THEN count + 1 ELSE 1 END,
                    window_start = :window
                WHERE window_start != :window OR count < :limit
            '''), {"key": db.token_digest(key), "window": window, "limit": limit})
            allowed = allowed and result.rowcount == 1
    return allowed


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(APP_ORIGIN + path, status_code=303, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


async def auth_endpoint(request: Request):
    # Required Origin verification protects login, registration, and logout from CSRF.
    # Missing/opaque origins are rejected rather than silently bypassing this check.
    if request.headers.get("origin") != APP_ORIGIN:
        return PlainTextResponse("Request origin is not allowed.", status_code=403)
    if request.headers.get("content-type", "").split(";")[0] != "application/x-www-form-urlencoded":
        return PlainTextResponse("Use the sign-in form.", status_code=415)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            return PlainTextResponse("Form is too large.", status_code=413)
    try:
        form = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=5)
    except (UnicodeError, ValueError):
        return PlainTextResponse("Invalid form.", status_code=400)
    action = request.path_params["action"]
    old_token = cookie_token(request.headers.get("cookie", ""))
    try:
        if action == "logout":
            await run_in_threadpool(revoke_session, old_token)
            response = redirect("/login")
            response.delete_cookie(COOKIE_NAME, path="/", secure=HTTPS, httponly=True, samesite="lax")
            return response
        if action not in ("login", "register"):
            return PlainTextResponse("Not found.", status_code=404)
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]
        ip = request.client.host if request.client else "unknown"
        allowed = await run_in_threadpool(allow_auth_request, ip, username, action == "register")
        if not allowed:
            return redirect(f"/{action}?error=invalid")
        if action == "register":
            user_id = await run_in_threadpool(register, username, password)
        else:
            user_id = await run_in_threadpool(authenticate, username, password)
        if user_id is None:
            return redirect("/login?error=invalid")
        token = await run_in_threadpool(issue_session, user_id, old_token)
        response = redirect("/")
        response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, path="/", secure=HTTPS, httponly=True, samesite="lax")
        return response
    except (ValueError, IntegrityError):
        return redirect(f"/{action}?error=invalid")
    except (SQLAlchemyError, OSError):
        # Do not log exception parameters: password hashes and token hashes are private.
        if action == "logout":
            return PlainTextResponse("Could not log out. Please try again.", status_code=503, headers={"Cache-Control": "no-store"})
        return redirect(f"/{action}?error=unavailable")


def create_auth_api() -> Starlette:
    return Starlette(routes=[Route("/auth/{action}", auth_endpoint, methods=["POST"])])
