"""Persistence checks use temporary SQLite files, never personal history."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4
from threading import Barrier

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, select

from learnloop import database as db
from learnloop.questions import BANK
from learnloop.state import QuizState


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "history.db"
        self.engine = db.make_engine(self.path)
        self.addCleanup(self.engine.dispose)
        db.initialize(self.engine)
        engine_patch = patch("learnloop.database.engine", self.engine)
        engine_patch.start()
        self.addCleanup(engine_patch.stop)

    def submit(self, correct=4):
        state = QuizState(_reflex_internal_init=True)
        state.choose_subject("python")
        state.start()
        for index, question in enumerate(BANK["python"]):
            if index < correct:
                state.select_answer(question.id, question.correct_id)
            state.next()
        state.request_submit()
        state.submit()
        return state

    def test_empty_history_and_progress(self):
        self.assertEqual(db.history(), [])
        self.assertEqual(db.summary([]), {"count": 0, "average": None, "best": None, "latest": None, "subjects": []})
        state = QuizState(_reflex_internal_init=True)
        state.load_progress()
        self.assertEqual(state.stage, "progress")
        self.assertEqual((state.completed, state.history_items, state.error), (0, [], ""))
        state.choose_subject("python")
        state.start()
        self.assertEqual(db.history(), [])  # Starting alone never saves.

    def test_submit_history_snapshot_and_repeat_initialization(self):
        state = self.submit()
        self.assertEqual(state.stage, "results")
        attempt_id = state._attempt_id
        self.assertEqual(state.score, 4)
        self.assertTrue(state.saved_date.endswith("UTC"))
        original = db.get_attempt(attempt_id)
        self.assertEqual(datetime.fromisoformat(original["submitted_at"]).utcoffset().total_seconds(), 0)
        self.assertEqual(len(original["review"]), 10)
        self.assertEqual(original["review"][4]["selected"], "Not answered")
        with Session(self.engine) as session:
            rows = session.exec(select(db.Answer)).all()
            self.assertEqual(len(rows), 10)
            self.assertEqual(len(json.loads(rows[0].options_json)), 4)
        db.initialize(self.engine)
        state.load_progress()
        self.assertEqual(state.completed, 1)
        self.assertEqual(state.history_items[0]["id"], attempt_id)
        self.assertEqual(state.average, "40.0%")
        changed = tuple(replace(q, prompt="New text", explanation="New explanation", correct_id=q.options[0][0]) for q in BANK["python"])
        with patch.dict(BANK, {"python": changed}):
            self.assertEqual(db.get_attempt(attempt_id), original)
            state.view_saved(attempt_id)
            self.assertEqual(state.review, original["review"])
            self.assertEqual(state.score, 4)
            self.assertEqual(db.save_attempt(attempt_id, "python", {}), original)
        state.submit()
        self.assertEqual(len(db.history()), 1)

    def test_unique_primary_key_and_idempotent_retry(self):
        state = self.submit()
        original = db.get_attempt(state._attempt_id)
        self.assertEqual(db.save_attempt(state._attempt_id, "python", {}), original)
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session:
                session.add(db.Attempt(id=state._attempt_id, subject_id="python", subject_name="Python", score=0, total=10, submitted_at=datetime.now(UTC).isoformat()))
                session.commit()
        self.assertEqual(len(db.history()), 1)
        with Session(self.engine) as session:
            self.assertEqual(len(session.exec(select(db.Answer)).all()), 10)

    def test_simultaneous_submissions_save_one_attempt(self):
        attempt_id = str(uuid4())
        barrier = Barrier(2)
        original_get = db.get_attempt

        def both_see_missing(id, db_engine=None):
            result = original_get(id, db_engine)
            if result is None:
                barrier.wait(timeout=5)
            return result

        with patch("learnloop.database.get_attempt", side_effect=both_see_missing):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(db.save_attempt, attempt_id, "python", {}, self.engine) for _ in range(2)]
                results = [future.result(timeout=10) for future in futures]
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(db.history()), 1)
        self.assertEqual(len(results[0]["review"]), 10)

    def test_retry_when_commit_succeeded_but_response_was_lost(self):
        original_save = db.save_attempt

        def lost_response(*args):
            original_save(*args)
            raise RuntimeError("Connection lost after committing")

        with patch("learnloop.state.save_attempt", side_effect=lost_response):
            with self.assertLogs("learnloop.state", level="ERROR"):
                state = self.submit()
        self.assertEqual(state.stage, "confirm")
        self.assertEqual(len(db.history()), 1)
        state.submit()
        self.assertEqual(state.stage, "results")
        self.assertEqual(state.score, 4)
        self.assertEqual(len(db.history()), 1)

    def test_database_failure_rolls_back_and_ui_can_retry(self):
        # Abort partway through answer insertion, after the attempt row was flushed.
        with self.engine.begin() as connection:
            connection.exec_driver_sql("CREATE TRIGGER fail_answer BEFORE INSERT ON answer WHEN NEW.position = 4 BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with self.assertLogs("learnloop.state", level="ERROR"):
            state = self.submit()
        attempt_id = state._attempt_id
        self.assertEqual(state.stage, "confirm")
        self.assertIn("could not be saved", state.error)
        self.assertEqual(state.review, [])
        self.assertEqual(state.saved_date, "")
        self.assertEqual(state.answered, 4)
        with Session(self.engine) as session:
            self.assertEqual(session.exec(select(db.Attempt)).all(), [])
            self.assertEqual(session.exec(select(db.Answer)).all(), [])
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TRIGGER fail_answer")
        state.submit()
        self.assertEqual(state.stage, "results")
        self.assertEqual(state._attempt_id, attempt_id)
        self.assertEqual(state.score, 4)
        self.assertEqual(len(db.history()), 1)

    def test_error_loading_history_does_not_claim_empty_success(self):
        state = QuizState(_reflex_internal_init=True)
        with patch("learnloop.state.history", side_effect=OperationalError("test", {}, Exception("unavailable"))):
            with self.assertLogs("learnloop.state", level="ERROR"):
                state.load_progress()
        self.assertIn("Could not load", state.error)

    def test_summary_is_mean_of_percentages_and_history_newest_first(self):
        # Different totals distinguish mean percentages from pooled points.
        samples = [("python", 1, 2, "2026-01-01T10:00:00+00:00"),
                   ("python", 9, 10, "2026-01-02T10:00:00+00:00"),
                   ("sql", 0, 10, "2026-01-03T10:00:00+00:00")]
        with Session(self.engine) as session:
            for subject, score, total, date in samples:
                session.add(db.Attempt(id=str(uuid4()), subject_id=subject, subject_name=db.SUBJECTS[subject], score=score, total=total, submitted_at=date))
            session.commit()
        rows = db.history()
        self.assertEqual([row["score"] for row in rows], [0, 9, 1])
        result = db.summary(rows)
        self.assertEqual(result["count"], 3)
        self.assertAlmostEqual(result["average"], (50 + 90 + 0) / 3)
        self.assertEqual(result["best"], 90)
        self.assertEqual(result["latest"], "2026-01-03 10:00:00 UTC")
        by_name = {row["name"]: row for row in result["subjects"]}
        self.assertEqual(by_name["Python"]["average"], "70.0%")
        self.assertEqual(by_name["SQL"]["best"], "0.0%")
        self.assertEqual(by_name["Computer Fundamentals"]["average"], "No attempts yet")
        state = QuizState(_reflex_internal_init=True)
        state.load_progress()
        self.assertEqual((state.completed, state.average, state.best), (3, "46.7%", "90.0%"))

    def test_persistence_after_fresh_process_restart(self):
        state = self.submit(7)
        self.engine.dispose()
        # A fresh Python process has no shared Reflex state or SQLAlchemy engine.
        code = '''
import json, sys
from pathlib import Path
from learnloop import database as db
from learnloop.state import QuizState
db.engine = db.make_engine(Path(sys.argv[1]))
s = QuizState(_reflex_internal_init=True)
s.load_progress()
assert s.completed == 1
s.view_saved(sys.argv[2])
assert s.score == 7 and len(s.review) == 10 and not s.error
print(json.dumps({"score": s.score, "review": s.review}))
db.engine.dispose()
'''
        result = subprocess.run([sys.executable, "-c", code, str(self.path), state._attempt_id], check=True, capture_output=True, text=True)
        saved = json.loads(result.stdout)
        self.assertEqual(saved["score"], 7)
        self.assertEqual(saved["review"], state.review)


if __name__ == "__main__":
    unittest.main()
