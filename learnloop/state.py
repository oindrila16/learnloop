"""Session-specific quiz state and server-side event handlers."""

import reflex as rx

from .questions import BANK, SUBJECTS, grade


class QuizState(rx.State):
    # Underscore fields stay on the backend and are never browser state.
    _subject_id: str = ""
    _answers: dict[str, str] = {}
    _position: int = 0
    _stage: str = "home"

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
    percentage: int = 0
    review: list[dict[str, str]] = []

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
        self._set_stage("home")

    @rx.event
    def choose_subject(self, subject_id: str):
        if not isinstance(subject_id, str) or subject_id not in BANK:
            return
        self.home()
        self._subject_id = subject_id
        self.subject_name = SUBJECTS[subject_id]
        self._set_stage("intro")

    @rx.event
    def start(self):
        if self._stage not in ("intro", "results") or self._subject_id not in BANK:
            return
        self._answers = {}
        self._position = 0
        self.score = 0
        self.percentage = 0
        self.review = []
        self._set_stage("quiz")
        self._show_question()

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

    @rx.event
    def next(self):
        if self._stage == "quiz" and self._position < 9:
            self._position += 1
            self._show_question()

    @rx.event
    def request_submit(self):
        if self._stage == "quiz" and self._position == 9:
            self._set_stage("confirm")

    @rx.event
    def cancel_submit(self):
        if self._stage == "confirm":
            self._set_stage("quiz")

    @rx.event
    def submit(self):
        if self._stage != "confirm" or self._subject_id not in BANK:
            return
        self.score, self.review = grade(self._subject_id, self._answers)
        self.percentage = self.score * 100 // len(BANK[self._subject_id])
        self._set_stage("results")
