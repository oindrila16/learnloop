"""Authentication and isolation checks against temporary databases."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from reflex.istate.data import HeaderData
from reflex.state import StateUpdate
from reflex_base.utils.serializers import serialize
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from starlette.testclient import TestClient

from learnloop import auth, database as db
from learnloop.questions import BANK
from learnloop.security import SessionBoundary
from learnloop.settings import APP_ORIGIN, BACKEND_ORIGIN, COOKIE_NAME
from learnloop.state import QuizState
from support import authenticated_state, new_account

PASSWORD = "a long test password only"


class AuthTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.engine = db.make_engine(Path(temporary.name) / "test.db")
        self.addCleanup(self.engine.dispose)
        db.initialize(self.engine)
        engine_patch = patch("learnloop.database.engine", self.engine)
        engine_patch.start()
        self.addCleanup(engine_patch.stop)
        self.client = TestClient(auth.create_auth_api(), base_url=BACKEND_ORIGIN, follow_redirects=False)
        self.addCleanup(self.client.close)

    def post(self, action, username="alice", password=PASSWORD, client=None):
        return (client or self.client).post("/auth/" + action, data={"username": username, "password": password}, headers={"Origin": APP_ORIGIN})

    def complete(self, token, correct=3):
        state = authenticated_state(token)
        state.choose_subject("python")
        state.start()
        for i, q in enumerate(BANK["python"]):
            if i < correct:
                state.select_answer(q.id, q.correct_id)
            state.next()
        state.request_submit()
        list(state.submit())
        self.assertEqual(state.stage, "results")
        return state

    def test_register_duplicate_normalized_username_and_password_hash(self):
        response = self.post("register", "Alice")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], APP_ORIGIN + "/")
        cookie = response.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)
        self.assertIn("Max-Age=28800", cookie)
        self.assertNotIn("Secure", cookie)  # Loopback HTTP development only.
        token = self.client.cookies.get(COOKIE_NAME)
        user = db.current_user(token)
        self.assertEqual(user["username"], "alice")
        with Session(self.engine) as session:
            row = session.get(db.Learner, user["id"])
            self.assertTrue(row.password_hash.startswith("$argon2id$"))
            self.assertNotEqual(row.password_hash, PASSWORD)
            login = session.exec(select(db.LoginSession)).one()
            self.assertNotEqual(login.token_hash, token)
            self.assertEqual(login.token_hash, db.token_digest(token))
        duplicate = self.post("register", " ALICE ")
        self.assertEqual(duplicate.headers["location"], APP_ORIGIN + "/register?error=invalid")
        self.assertEqual(db.current_user(token)["id"], user["id"])
        with Session(self.engine) as session:
            self.assertEqual(len(session.exec(select(db.Learner)).all()), 1)

    def test_valid_invalid_login_and_rotation(self):
        self.post("register")
        old_token = self.client.cookies.get(COOKIE_NAME)
        invalid = self.post("login", password="wrong password")
        missing = self.post("login", username="unknown", password="wrong password")
        self.assertEqual(invalid.headers["location"], missing.headers["location"])
        valid = self.post("login")
        self.assertEqual(valid.headers["location"], APP_ORIGIN + "/")
        token = self.client.cookies.get(COOKIE_NAME)
        self.assertNotEqual(token, old_token)
        self.assertEqual(db.current_user(token)["username"], "alice")
        with self.assertRaises(db.AuthenticationRequired):
            db.current_user(old_token)

    def test_logout_invalidates_stale_session_and_clears_cached_state(self):
        self.post("register")
        token = self.client.cookies.get(COOKIE_NAME)
        state = self.complete(token)
        response = self.post("logout")
        self.assertEqual(response.status_code, 303)
        self.assertIn("Max-Age=0", response.headers["set-cookie"])
        for read in (lambda: db.current_user(token), lambda: db.history(token), lambda: db.get_attempt(state._attempt_id, token)):
            with self.assertRaises(db.AuthenticationRequired):
                read()
        list(state.load_progress())  # The socket still has the old cookie header.
        self.assertEqual(state.stage, "login")
        self.assertEqual((state.review, state.history_items, state.username, state._answers), ([], [], "", {}))

    def test_expired_session_denies_reads_writes_and_new_quiz(self):
        user_id, token = new_account()
        state = self.complete(token)
        with Session(self.engine) as session:
            login = session.get(db.LoginSession, db.token_digest(token))
            login.expires_at = int(time.time()) - 1
            session.add(login)
            session.commit()
        with self.assertRaises(db.AuthenticationRequired):
            db.history(token)
        with self.assertRaises(db.AuthenticationRequired):
            db.save_attempt(str(uuid4()), "python", {}, token)
        state.start()
        self.assertEqual(state.stage, "login")
        self.assertEqual(state.review, [])

    def test_two_learners_have_private_results_and_cannot_guess_ids(self):
        alice_id, alice_token = new_account("alice")
        bob_id, bob_token = new_account("bob")
        alice = self.complete(alice_token, 8)
        bob = self.complete(bob_token, 2)
        alice_attempt = alice._attempt_id
        bob_attempt = bob._attempt_id
        self.assertEqual([row["id"] for row in db.history(alice_token)], [alice_attempt])
        self.assertEqual([row["id"] for row in db.history(bob_token)], [bob_attempt])
        self.assertIsNone(db.get_attempt(alice_attempt, bob_token))
        list(bob.load_progress())
        list(bob.view_saved(alice_attempt))
        self.assertIn("could not be found", bob.error)
        self.assertEqual(bob.review, [])
        with self.assertRaises(IntegrityError):
            db.save_attempt(alice_attempt, "python", {}, bob_token)
        self.assertEqual(db.get_attempt(alice_attempt, alice_token)["score"], 8)
        with Session(self.engine) as session:
            self.assertEqual(session.get(db.Attempt, alice_attempt).user_id, alice_id)
            self.assertEqual(session.get(db.Attempt, bob_attempt).user_id, bob_id)

    def test_unauthenticated_and_forged_display_flags_do_not_authorize(self):
        state = QuizState(_reflex_internal_init=True)
        state.username = "alice"  # Display text is never trusted.
        state.choose_subject("python")
        self.assertEqual(state.stage, "login")
        with self.assertRaises(db.AuthenticationRequired):
            db.history("")
        with self.assertRaises(db.AuthenticationRequired):
            db.save_attempt(str(uuid4()), "python", {}, "not-a-real-token")
        with self.assertRaises(db.AuthenticationRequired):
            db.get_attempt(str(uuid4()), "")

    def test_account_switch_clears_active_and_completed_data(self):
        _, alice_token = new_account("alice")
        _, bob_token = new_account("bob")
        state = self.complete(alice_token)
        state.rx_router_headers = HeaderData(cookie=f"{COOKIE_NAME}={bob_token}")
        list(state.load_progress())
        self.assertEqual((state.username, state.completed, state.review, state._answers), ("bob", 0, [], {}))
        state.choose_subject("python")
        state.start()
        state.select_answer("py-01", "py-01-b")
        state.rx_router_headers = HeaderData(cookie=f"{COOKIE_NAME}={alice_token}")
        state.next()
        self.assertEqual(state.username, "alice")
        self.assertEqual((state.stage, state._answers, state._attempt_id), ("home", {}, ""))

    def test_rate_limits_persist_and_do_not_trust_forwarded_ip(self):
        self.post("register")
        for _ in range(5):
            self.post("login", password="wrong password")
        blocked = self.post("login")
        self.assertIn("error=invalid", blocked.headers["location"])
        self.engine.dispose()
        self.assertFalse(auth.allow_auth_request("another-ip", "alice"))
        with patch("learnloop.auth.time.time", return_value=time.time() + 901):
            self.assertTrue(auth.allow_auth_request("another-ip", "alice"))
        for i in range(31):
            self.client.post("/auth/login", data={"username": f"user{i}", "password": PASSWORD}, headers={"Origin": APP_ORIGIN, "X-Forwarded-For": f"192.0.2.{i}"})
        with patch("learnloop.auth.authenticate") as authenticate:
            self.post("login", "one-more-user")
            authenticate.assert_not_called()

    def test_csrf_logout_get_and_body_limits(self):
        for headers in ({}, {"Origin": "https://evil.example"}, {"Origin": "null"}):
            response = self.client.post("/auth/register", data={"username": "alice", "password": PASSWORD}, headers=headers)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/auth/logout").status_code, 405)
        response = self.client.post("/auth/login", content="x" * 5000, headers={"Origin": APP_ORIGIN, "Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(response.status_code, 413)

    def test_https_cookie_attributes_and_failed_logout(self):
        with patch("learnloop.auth.HTTPS", True), patch("learnloop.auth.COOKIE_NAME", "__Host-learnloop_session"):
            response = self.post("register")
        cookie = response.headers["set-cookie"]
        for attribute in ("__Host-learnloop_session=", "Secure", "HttpOnly", "Path=/", "SameSite=lax"):
            self.assertIn(attribute, cookie)
        self.assertNotIn("Domain=", cookie)
        with patch("learnloop.auth.revoke_session", side_effect=OSError("unavailable")):
            response = self.post("logout")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("set-cookie", response.headers)

    def test_cookie_is_not_serialized_to_browser(self):
        _, token = new_account()
        state = authenticated_state(token)
        self.assertNotIn(token, json.dumps(serialize(state.router.headers)))
        self.assertNotIn(token, json.dumps(state.dict()))

    def test_boundary_clears_before_hydration_and_after_expiry(self):
        _, token = new_account()
        state = self.complete(token)

        class Root:
            async def get_state(self, kind):
                return state
            def dict(self):
                return state.dict()

        boundary = SessionBoundary()
        auth.revoke_session(token)
        asyncio.run(boundary.preprocess(None, Root(), None))
        self.assertEqual(state.review, [])
        self.assertEqual(state.username, "")
        # A response built just before expiry must be discarded too.
        _, token2 = new_account("another")
        state = self.complete(token2)
        auth.revoke_session(token2)
        update = StateUpdate(delta={"private": "stale"}, events=[])
        result = asyncio.run(boundary.postprocess(None, Root(), None, update))
        self.assertNotIn("stale", json.dumps(result.delta))

    def test_non_destructive_legacy_migration_and_no_automatic_claim(self):
        legacy_path = Path(self.engine.url.database).with_name("legacy.db")
        legacy = db.make_engine(legacy_path)
        self.addCleanup(legacy.dispose)
        with legacy.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE attempt (id VARCHAR PRIMARY KEY, subject_id VARCHAR NOT NULL, subject_name VARCHAR NOT NULL, score INTEGER NOT NULL, total INTEGER NOT NULL, submitted_at VARCHAR NOT NULL)")
            connection.exec_driver_sql("INSERT INTO attempt VALUES ('legacy-1', 'python', 'Python', 4, 10, '2026-01-01T00:00:00+00:00')")
            connection.exec_driver_sql("CREATE TABLE answer (attempt_id VARCHAR NOT NULL REFERENCES attempt(id), question_id VARCHAR NOT NULL, position INTEGER NOT NULL, prompt VARCHAR NOT NULL, options_json VARCHAR NOT NULL, correct_id VARCHAR NOT NULL, selected_id VARCHAR, explanation VARCHAR NOT NULL, PRIMARY KEY (attempt_id, question_id))")
            connection.exec_driver_sql("INSERT INTO answer VALUES ('legacy-1', 'py-01', 0, 'Original question', '[[\"a\", \"First\"], [\"b\", \"Second\"], [\"c\", \"Third\"], [\"d\", \"Fourth\"]]', 'a', 'b', 'Original explanation')")
        db.initialize(legacy)
        db.initialize(legacy)
        with patch("learnloop.database.engine", legacy):
            _, token = new_account()
            self.assertEqual(db.history(token), [])
            self.assertIsNone(db.get_attempt("legacy-1", token))
        with legacy.connect() as connection:
            self.assertEqual(connection.exec_driver_sql("SELECT id, score, user_id FROM attempt").all(), [("legacy-1", 4, None)])
            self.assertEqual(connection.exec_driver_sql("PRAGMA user_version").scalar(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT prompt, explanation FROM answer").all(), [("Original question", "Original explanation")])


if __name__ == "__main__":
    unittest.main()
