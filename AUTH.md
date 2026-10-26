# Accounts and private history

LearnLoop uses the Starlette backend already included with Reflex 0.10.0.
`pwdlib[argon2]` hashes passwords with Argon2id. SQLModel stores accounts and
sessions in the same SQLite database as quiz attempts.

I checked reflex-local-auth too. Its current implementation uses local-storage
tokens and the older Reflex database API. Using it here would need changes to
meet the cookie and database requirements. Reflex's enterprise authentication
uses an external identity provider, which this version doesn't need.

## How login works

- Usernames are 3–30 ASCII letters, numbers, or underscores. They are saved in
  lowercase and must be unique. Passwords must be 15–128 characters.
- The login and registration forms send normal HTTP POST requests. Passwords
  aren't copied into Reflex state or browser local storage.
- A successful login creates a fresh random 256-bit session token. Only its
  SHA-256 hash is stored in the session table. Changing accounts replaces the
  previous session for that browser.
- The cookie is HttpOnly, SameSite=Lax, host-only, and scoped to `/`. It expires
  after eight hours, and the server checks its expiry on each private action.
- Logout is a POST request that deletes the server session and clears the cookie.
  An already-open connection with the old cookie cannot read or save data.
- Login, registration, and logout require an exact matching Origin header.
  Missing or different origins are rejected. WebSocket origins are restricted
  to the configured frontend origin too.
- Login is limited to five tries per username and 30 per network peer per
  15-minute window. Registration is limited to ten per peer per window. The
  limits include successful requests and survive app restarts. Login failures
  use the same message for unknown users, wrong passwords, and rate limits.

Every history query and saved-result lookup checks a valid session and filters by
its user. Saving an attempt derives the owner from that same session. There is
no browser-supplied user ID. Cached quiz and history data is cleared before
hydration when the session changes or is no longer valid.

## Local HTTP development

The defaults are:

```sh
LEARNLOOP_APP_ORIGIN=http://localhost:3000
LEARNLOOP_BACKEND_ORIGIN=http://localhost:8000
LEARNLOOP_HTTPS=0
```

The development cookie is named `learnloop_session`. Secure is off because this
is HTTP; HttpOnly and SameSite=Lax are still on. HTTP mode only accepts loopback
hostnames in configuration. Use it on your own computer, not for public hosting.

For different ports, export the origins before starting Reflex:

```sh
export LEARNLOOP_APP_ORIGIN=http://localhost:3011
export LEARNLOOP_BACKEND_ORIGIN=http://localhost:8011
uv run reflex run --frontend-port 3011 --backend-port 8011 --backend-host 127.0.0.1
```

The frontend and backend must use the same hostname. Cookies don't distinguish
ports, so use a dedicated hostname when hosting alongside other applications.

## HTTPS hosting settings

For example, with a reverse proxy serving one HTTPS hostname:

```sh
export LEARNLOOP_HTTPS=1
export LEARNLOOP_APP_ORIGIN=https://learnloop.example.com
export LEARNLOOP_BACKEND_ORIGIN=https://learnloop.example.com
```

This uses a Secure, HttpOnly `__Host-learnloop_session` cookie. It has no Domain
attribute and uses Path=/ and SameSite=Lax. Configuration fails if either URL is
HTTP in this mode. No application signing secret is needed: tokens are random
identifiers checked against server-side records, not signed browser data.

The proxy must route `/auth/*` and `/_event/*` to the backend, support WebSocket
upgrades, and preserve Cookie and Origin headers. Serve everything over HTTPS
and keep the backend private. These settings aren't a complete deployment guide.

## Database migration

Stop the app and back up `learnloop.db` before upgrading. Run:

```sh
uv run python -m learnloop.database
```

Migration 1 creates `learner`, `loginsession`, and `loginbucket`, adds the nullable
`attempt.user_id` foreign key and its index, and records SQLite user_version=1.
It never drops tables, deletes answers, or assigns existing attempts to an account.
It checks for the column before adding it, so running it again is safe. New
databases get the same schema through this command.

Old attempts have user_id=NULL and are unavailable through learner pages. They
remain in the database and backups. There is no automatic claiming feature.
Backups now contain password hashes and session hashes too; keep them private.

## Limits

This version has no password recovery, email, MFA, or account-management tools.
SQLite and the built-in rate limits are intended for a small installation. Behind
a proxy, the peer limit may be shared by all learners: the app deliberately does
not trust arbitrary X-Forwarded-For headers. Public hosting needs proxy-level
abuse protection, monitoring, backups, and a security review.

An idle tab may still display information already loaded before logout in another
tab. Its next server interaction validates the session and clears private state.
Information already delivered to a browser cannot be taken back. Refreshing or
logging out in that tab clears the view. App logout cannot erase saved browser
password-manager entries.

The tests cover account isolation, session expiry/revocation, migration, guessing
limits, CSRF origin checks, and the actual Reflex socket event path. Visual
browser login and keyboard checks have not been performed in this environment.

References: [Reflex API transformer](https://reflex.dev/docs/api-routes/overview/),
[server cookie headers](https://reflex.dev/docs/utility-methods/router-attributes/),
[pwdlib](https://frankie567.github.io/pwdlib/guide/),
[Starlette cookies](https://starlette.dev/responses/), and
[Origin checks](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
