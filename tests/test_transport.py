"""Exercise Reflex's real event pipeline, including the pre-hydration guard."""

import json
from pathlib import Path
import signal
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from starlette.testclient import TestClient

from learnloop import database as db
from learnloop.settings import APP_ORIGIN, BACKEND_ORIGIN, COOKIE_NAME
from learnloop.state import QuizState


class TransportTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(signal, "alarm"), "This bounded socket check uses POSIX alarms")
    def test_socket_cookie_authorization_and_logout(self):
        from learnloop.learnloop import app

        signal.alarm(30)
        try:
            with TemporaryDirectory() as directory:
                engine = db.make_engine(Path(directory) / "transport.db")
                self.addCleanup(engine.dispose)
                db.initialize(engine)
                with patch("learnloop.database.engine", engine), TestClient(app(), base_url=BACKEND_ORIGIN, follow_redirects=False) as client:
                    response = client.post("/auth/register", data={"username": "socket_learner", "password": "a long socket test password"}, headers={"Origin": APP_ORIGIN})
                    self.assertEqual(response.status_code, 303)
                    login = client.cookies.get(COOKIE_NAME)
                    transport = str(uuid4())
                    headers = {"Origin": APP_ORIGIN, "Upgrade": "websocket", "Connection": "Upgrade", "Cookie": f"{COOKIE_NAME}={login}"}
                    with client.websocket_connect("/_event/?EIO=4&transport=websocket&token=" + transport, headers=headers) as socket:
                        self.assertTrue(socket.receive_text().startswith("0"))
                        socket.send_text("40/_event,")
                        self.assertTrue(socket.receive_text().startswith("40/_event,"))

                        def action(name, payload, expected):
                            event = {"token": transport, "name": QuizState.get_full_name() + "." + name,
                                     "payload": payload,
                                     "router_data": {"pathname": "/", "asPath": "/", "headers": {"cookie": "forged"}}}
                            socket.send_text("42/_event," + json.dumps(["event", event]))
                            for _ in range(20):
                                message = socket.receive_text()
                                if message == "2":
                                    socket.send_text("3")
                                    continue
                                self.assertNotIn(login, message)
                                if message.startswith("42/_event,") and expected in message:
                                    return
                            self.fail("Expected state update was not received")

                        action("choose_subject", {"subject_id": "python"}, "intro")
                        # Revoke through HTTP, then reuse the already-open socket.
                        logged_out = client.post("/auth/logout", data={}, headers={"Origin": APP_ORIGIN, "Content-Type": "application/x-www-form-urlencoded"})
                        self.assertEqual(logged_out.status_code, 303)
                        action("start", {}, 'login')
                        with self.assertRaises(db.AuthenticationRequired):
                            db.history(login)
        finally:
            signal.alarm(0)
