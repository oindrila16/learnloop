"""Session-specific quiz state and server-side event handlers."""

import reflex as rx
import logging
from uuid import UUID, uuid4
from sqlalchemy.exc import SQLAlchemyError

from .questions import BANK, SUBJECTS
from .database import get_attempt, history, save_attempt, summary

logger = logging.getLogger(__name__)


class QuizState(rx.State):
    # Underscore fields stay on the backend and are never browser state.
    _subject_id: str = ""
    _answers: dict[str, str] = {}
    _position: int = 0
    _stage: str = "home"
    _attempt_id: str = ""
    _destination: str = "/"

    stage: str = "home"
    subject_name: str = ""
    question_id: str = ""
    prompt: str = ""
    options: list[dict[str, str]] = []
    selected_id: str = ""
    number: int = 1
    total: int = 10
    answered: int = 0
    score: int = 0
    percentage: float = 0
    review: list[dict[str, str]] = []
    error: str = ""
    saved_date: str = ""
    history_items: list[dict[str, str]] = []
    subject_summaries: list[dict[str, str]] = []
    completed: int = 0
    average: str = ""
    best: str = ""
    latest: str = ""
    saving: bool = False
    loading: bool = False
    discard_open: bool = False
    history_error: bool = False

    @rx.event
    def navigate(self, destination: str):
        if self.saving or self.loading or destination not in ("/", "/progress"):
            return
        if self._stage in ("quiz", "confirm"):
            self._destination = destination
            self.discard_open = True
            return
        # Explicitly load even when the destination URL is already open.
        event = QuizState.home if destination == "/" else QuizState.load_progress
        return [event, rx.redirect(destination)]

    @rx.event
    def set_discard_open(self, value: bool):
        self.discard_open = value
        if not value and self._stage in ("quiz", "confirm"):
            target = "question-heading" if self._stage == "quiz" else "confirmation-heading"
            return rx.set_focus(target)

    @rx.event
    def confirm_discard(self):
        if not self.discard_open or self.saving:
            return
        destination = self._destination
        self.home()
        event = QuizState.home if destination == "/" else QuizState.load_progress
        return [event, rx.redirect(destination)]

    @rx.event
    def load_results(self):
        if self._stage == "results" and self.review and self.saved_date:
            return
        self.home()
        self._set_stage("unavailable")
        self.error = "There is no result to show here. Open a saved attempt from Progress, or start a quiz from Home."

    def _set_stage(self, stage: str):
        self._stage = stage
        self.stage = stage

    def _show_question(self):
        q = BANK[self._subject_id][self._position]
        self.question_id = q.id
        self.prompt = q.prompt
        self.options = [{"id": id, "text": text} for id, text in q.options]
        self.selected_id = self._answers.get(q.id, "")
        self.number = self._position + 1
        self.answered = len(self._answers)

    @rx.event
    def home(self):
        self.saving = False
        self.loading = False
        self.discard_open = False
        self.history_error = False
        self._attempt_id = ""
        self._subject_id = ""
        self._answers = {}
        self._position = 0
        self.subject_name = ""
        self.question_id = ""
        self.prompt = ""
        self.options = []
        self.selected_id = ""
        self.number = 1
        self.answered = 0
        self.score = 0
        self.percentage = 0
        self.review = []
        self.error = ""
        self.saved_date = ""
        self.history_items = []
        self.subject_summaries = []
        self.completed = 0
        self.average = ""
        self.best = ""
        self.latest = ""
        self._set_stage("home")

    @rx.event
    def choose_subject(self, subject_id: str):
        if not isinstance(subject_id, str) or subject_id not in BANK:
            self.error = "That subject is not available. Choose Python, SQL, or Computer Fundamentals from Home."
            return
        if self._stage in ("quiz", "confirm") or self.saving:
            return
        self.home()
        self._subject_id = subject_id
        self.subject_name = SUBJECTS[subject_id]
        self._set_stage("intro")

    @rx.event
    def start(self):
        if self._stage not in ("intro", "results") or self._subject_id not in BANK:
            if self._stage == "results":
                self.error = "This subject is no longer available. Choose a subject from Home."
            return
        self._answers = {}
        self._attempt_id = str(uuid4())
        self._position = 0
        self.score = 0
        self.percentage = 0
        self.review = []
        self.error = ""
        self.saved_date = ""
        self.total = len(BANK[self._subject_id])
        self._set_stage("quiz")
        self._show_question()
        return rx.set_focus("question-heading")

    @rx.event
    def select_answer(self, question_id: str, option_id: str):
        if self._stage != "quiz" or self._subject_id not in BANK:
            return
        q = BANK[self._subject_id][self._position]
        if question_id != q.id or not isinstance(option_id, str) or option_id not in dict(q.options):
            return
        self._answers[q.id] = option_id
        self._show_question()

    @rx.event
    def previous(self):
        if self._stage == "quiz" and self._position > 0:
            self._position -= 1
            self._show_question()
            return rx.set_focus("question-heading")

    @rx.event
    def next(self):
        if self._stage == "quiz" and self._position < 9:
            self._position += 1
            self._show_question()
            return rx.set_focus("question-heading")

    @rx.event
    def request_submit(self):
        if self._stage == "quiz" and self._position == 9:
            self._set_stage("confirm")
            return rx.set_focus("confirmation-heading")

    @rx.event
    def cancel_submit(self):
        if self._stage == "confirm" and not self.saving:
            self.error = ""
            self._set_stage("quiz")
            return rx.set_focus("question-heading")

    def _apply_result(self, saved: dict):
        self.subject_name = saved["subject_name"]
        self.score = saved["score"]
        self.total = saved["total"]
        self.percentage = saved["percentage"]
        self.review = saved["review"]
        self.saved_date = saved["date"]
        self.error = ""
        self._set_stage("results")

    @rx.event
    def submit(self):
        if self.saving or self.discard_open or self._stage != "confirm" or self._subject_id not in BANK:
            return
        self.saving = True
        self.error = ""
        yield  # Send the disabled controls and saving message before database work.
        try:
            saved = save_attempt(self._attempt_id, self._subject_id, self._answers)
        except (SQLAlchemyError, OSError, RuntimeError):
            logger.exception("Could not save quiz attempt")
            self.error = "Your attempt could not be saved. Your answers are still here. Check that the database is initialized and writable, then retry Submit quiz."
            return
        finally:
            self.saving = False
        self._apply_result(saved)
        yield rx.set_focus("results-heading")

    @rx.event
    def load_progress(self):
        self.home()
        self._set_stage("progress")
        self.loading = True
        yield
        try:
            attempts = history()
            totals = summary(attempts)
        except (SQLAlchemyError, OSError):
            logger.exception("Could not load quiz history")
            self.history_error = True
            self.error = "Could not load your history. Check that the database is initialized and readable, then try again."
            return
        finally:
            self.loading = False
        self.completed = totals["count"]
        if attempts:
            self.average = f"{totals['average']:.1f}%"
            self.best = f"{totals['best']:.1f}%"
            self.latest = totals["latest"]
        self.subject_summaries = [
            {key: str(value) for key, value in row.items()} for row in totals["subjects"]
        ]
        self.history_items = [
            {"id": row["id"], "subject": row["subject_name"], "date": row["date"],
             "score": f"{row['score']} / {row['total']}", "percentage": f"{row['percentage']:.1f}%"}
            for row in attempts
        ]

    @rx.event
    def view_saved(self, attempt_id: str):
        if self.loading or self.saving or self._stage in ("quiz", "confirm"):
            return
        try:
            UUID(attempt_id)
        except (ValueError, TypeError, AttributeError):
            self.error = "That attempt could not be found."
            return
        self.loading = True
        self.error = ""
        yield
        try:
            saved = get_attempt(attempt_id)
        except (SQLAlchemyError, OSError):
            logger.exception("Could not open saved attempt")
            self.error = "Could not open this result. Please try again."
            return
        finally:
            self.loading = False
        if saved is None:
            self.error = "That attempt could not be found."
            return
        self._subject_id = saved["subject_id"]
        self._apply_result(saved)
        yield rx.redirect("/results")
