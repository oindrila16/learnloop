"""Run with uv run python -m unittest discover -s tests -v."""

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from dataclasses import replace

from learnloop.questions import BANK, SUBJECTS, grade, validate_bank
from learnloop.state import QuizState
from learnloop.database import initialize, make_engine


class BankTests(unittest.TestCase):
    def test_bank_and_scoring(self):
        validate_bank()
        for subject, questions in BANK.items():
            with self.subTest(subject=subject):
                correct = {q.id: q.correct_id for q in questions}
                wrong = {q.id: next(id for id, _ in q.options if id != q.correct_id) for q in questions}
                self.assertEqual(grade(subject, correct)[0], 10)
                self.assertEqual(grade(subject, wrong)[0], 0)
                score, review = grade(subject, dict(list(correct.items())[:4]))
                self.assertEqual(score, 4)
                self.assertEqual(sum(r["selected"] == "Not answered" for r in review), 6)
                score, review = grade(subject, {})
                self.assertEqual(score, 0)
                self.assertTrue(all(r["selected"] == "Not answered" for r in review))
                self.assertEqual(len(review), 10)
                self.assertTrue(all(r["correct"] and r["explanation"] for r in review))

    def test_validation_rejects_broken_bank(self):
        q = BANK["python"][0]
        for broken in (
            replace(q, id=BANK["python"][1].id),
            replace(q, options=q.options[:3]),
            replace(q, options=(q.options[0],) * 4),
            replace(q, correct_id="missing"),
        ):
            bank = dict(BANK)
            bank["python"] = (broken, *BANK["python"][1:])
            with self.assertRaises(ValueError):
                validate_bank(bank, SUBJECTS)

    def test_grade_rejects_invalid_ids(self):
        for answers in ({"fake": "fake"}, {"py-01": "sql-01-a"}):
            with self.assertRaises(ValueError):
                grade("python", answers)


class FlowTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        db_engine = make_engine(Path(temporary.name) / "quiz.db")
        self.addCleanup(db_engine.dispose)
        initialize(db_engine)
        engine_patch = patch("learnloop.database.engine", db_engine)
        engine_patch.start()
        self.addCleanup(engine_patch.stop)
        self.state = QuizState(_reflex_internal_init=True)
        self.state.choose_subject("python")
        self.state.start()

    def test_browser_state_has_no_answer_key_before_submission(self):
        s = self.state
        for _ in range(10):
            serialized = json.dumps(s.dict())
            self.assertNotIn("correct_id", serialized)
            self.assertNotIn("explanation", serialized)
            self.assertNotIn("_answers", serialized)
            self.assertEqual(s.review, [])
            for questions in BANK.values():
                for q in questions:
                    self.assertNotIn(q.explanation, serialized)
            s.next()
        s.request_submit()
        self.assertEqual(s.review, [])

    def test_handler_scoring_for_each_subject(self):
        for subject, questions in BANK.items():
            for mode, expected in (("correct", 10), ("incorrect", 0), ("partial", 4), ("empty", 0)):
                with self.subTest(subject=subject, mode=mode):
                    s = QuizState(_reflex_internal_init=True)
                    s.choose_subject(subject)
                    s.start()
                    for index, q in enumerate(questions):
                        if mode == "correct" or (mode == "partial" and index < 4):
                            s.select_answer(q.id, q.correct_id)
                        elif mode == "incorrect":
                            s.select_answer(q.id, next(id for id, _ in q.options if id != q.correct_id))
                        s.next()
                    s.request_submit()
                    list(s.submit())
                    self.assertEqual((s.score, s.percentage), (expected, expected * 10))

    def test_navigation_and_validation(self):
        s = self.state
        first = BANK["python"][0]
        s.select_answer("fake", first.correct_id)
        s.select_answer(first.id, "fake")
        self.assertEqual(s.answered, 0)
        s.select_answer(first.id, first.correct_id)
        s.next()
        s.select_answer(first.id, first.correct_id)  # Stale question event.
        self.assertEqual(s.answered, 1)
        s.previous()
        self.assertEqual(s.selected_id, first.correct_id)
        self.assertEqual(s.number, 1)
        s.previous()
        self.assertEqual(s.number, 1)
        self.assertEqual(s.review, [])
        list(s.submit())  # No confirmation, no result.
        self.assertEqual(s.stage, "quiz")

    def test_submission_is_final_and_fresh_attempt_clears(self):
        s = self.state
        for q in BANK["python"]:
            s.select_answer(q.id, q.correct_id)
            s.next()
        self.assertEqual(s.number, 10)
        s.request_submit()
        self.assertEqual(s.stage, "confirm")
        self.assertEqual(s.review, [])
        s.cancel_submit()
        self.assertEqual(s.stage, "quiz")
        s.request_submit()
        list(s.submit())
        self.assertEqual((s.score, s.percentage), (10, 100))
        snapshot = list(s.review)
        s.select_answer("py-10", "py-10-a")
        s.previous()
        list(s.submit())
        self.assertEqual(s.review, snapshot)
        self.assertEqual(s.score, 10)
        s.start()
        self.assertEqual((s.number, s.answered, s.selected_id, s.score, s.review), (1, 0, "", 0, []))

    def test_all_unanswered_submission_and_session_isolation(self):
        s = self.state
        other = QuizState(_reflex_internal_init=True)
        other.choose_subject("sql")
        other.start()
        for _ in range(9):
            s.next()
        s.request_submit()
        self.assertEqual(s.total - s.answered, 10)
        list(s.submit())
        self.assertEqual((s.score, s.percentage), (0, 0))
        self.assertEqual(other.stage, "quiz")
        self.assertEqual(other.review, [])
        s.home()  # Page load resets safely.
        self.assertEqual((s.stage, s.review, s.options), ("home", [], []))
        s.choose_subject("fake")
        s.start()
        self.assertEqual(s.stage, "home")


if __name__ == "__main__":
    unittest.main()
