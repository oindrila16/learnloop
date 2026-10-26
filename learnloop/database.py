"""SQLite storage. Initialize explicitly with: uv run python -m learnloop.database"""

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .questions import BANK, SUBJECTS, grade

DB_PATH = Path(__file__).resolve().parent.parent / "learnloop.db"


def make_engine(path: Path):
    db_engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    @event.listens_for(db_engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return db_engine


engine = make_engine(DB_PATH)


class Learner(SQLModel, table=True):
    id: str = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str


class LoginSession(SQLModel, table=True):
    token_hash: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="learner.id", index=True)
    expires_at: int


class LoginBucket(SQLModel, table=True):
    key: str = Field(primary_key=True)
    window_start: int
    count: int


class AuthenticationRequired(Exception):
    """No current, valid server session."""


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_user(session: Session, token: str) -> Learner:
    """Resolve identity in the same short database session as the private query."""
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise AuthenticationRequired()
    login = session.get(LoginSession, token_digest(token))
    if login is None or login.expires_at <= int(time.time()):
        raise AuthenticationRequired()
    user = session.get(Learner, login.user_id)
    if user is None:
        raise AuthenticationRequired()
    return user


def current_user(token: str, db_engine=None) -> dict[str, str]:
    with Session(db_engine if db_engine is not None else engine) as session:
        user = session_user(session, token)
        return {"id": user.id, "username": user.username}


class Attempt(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str | None = Field(default=None, foreign_key="learner.id", index=True)
    subject_id: str
    subject_name: str
    score: int
    total: int
    # An ISO 8601 string with +00:00 preserves UTC explicitly in SQLite.
    submitted_at: str


class Answer(SQLModel, table=True):
    attempt_id: str = Field(foreign_key="attempt.id", primary_key=True)
    question_id: str = Field(primary_key=True)
    position: int
    prompt: str
    options_json: str
    correct_id: str
    selected_id: str | None = None
    explanation: str


def initialize(db_engine=None) -> None:
    """Create missing tables only. Never drop or clear existing data."""
    db_engine = db_engine if db_engine is not None else engine
    with db_engine.connect() as connection:
        if connection.exec_driver_sql("PRAGMA user_version").scalar() > 1:
            raise RuntimeError("This database uses a newer migration version.")
    SQLModel.metadata.create_all(db_engine)
    # Migration 1: SQLite can add a nullable foreign key without rebuilding rows.
    # NULL means an unassigned legacy attempt; no account is granted ownership.
    with db_engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(attempt)")}
        if "user_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE attempt ADD COLUMN user_id VARCHAR REFERENCES learner(id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_attempt_user_id ON attempt (user_id)")
        connection.exec_driver_sql("PRAGMA user_version=1")


def attempt_data(attempt: Attempt) -> dict:
    """Copy scalar data while the session is open; never return ORM objects."""
    return {
        "id": attempt.id,
        "subject_id": attempt.subject_id,
        "subject_name": attempt.subject_name,
        "score": attempt.score,
        "total": attempt.total,
        "percentage": attempt.score * 100 / attempt.total,
        "submitted_at": attempt.submitted_at,
        "date": datetime.fromisoformat(attempt.submitted_at).astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def get_attempt(attempt_id: str, token: str, db_engine=None) -> dict | None:
    with Session(db_engine if db_engine is not None else engine) as session:
        user = session_user(session, token)
        attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user.id)).first()
        if attempt is None:
            return None
        result = attempt_data(attempt)
        rows = session.exec(select(Answer).where(Answer.attempt_id == attempt_id).order_by(Answer.position)).all()
        review = []
        for row in rows:
            options = dict(json.loads(row.options_json))
            review.append({
                "id": row.question_id,
                "prompt": row.prompt,
                "selected": options.get(row.selected_id, "Not answered"),
                "correct": options[row.correct_id],
                "explanation": row.explanation,
                "outcome": "Correct" if row.selected_id == row.correct_id else "Incorrect",
                "options": " | ".join(options.values()),
            })
        result["review"] = review
        return result


def save_attempt(attempt_id: str, subject_id: str, answers: dict[str, str], token: str, db_engine=None) -> dict:
    """Persist once, returning the original snapshot if a submission is retried."""
    db_engine = db_engine if db_engine is not None else engine
    existing = get_attempt(attempt_id, token, db_engine)
    if existing is not None:
        return existing
    score, _ = grade(subject_id, answers)
    questions = BANK[subject_id]
    attempt = Attempt(
        id=attempt_id, subject_id=subject_id, subject_name=SUBJECTS[subject_id],
        score=score, total=len(questions), submitted_at=datetime.now(UTC).isoformat(),
    )
    try:
        with Session(db_engine) as session:
            with session.begin():
                user = session_user(session, token)
                attempt.user_id = user.id
                session.add(attempt)
                session.flush()
                for position, question in enumerate(questions):
                    session.add(Answer(
                        attempt_id=attempt_id, question_id=question.id, position=position,
                        prompt=question.prompt, options_json=json.dumps(question.options),
                        correct_id=question.correct_id, selected_id=answers.get(question.id),
                        explanation=question.explanation,
                    ))
                # The context commits both tables together, or rolls both back.
    except IntegrityError:
        # Another request may have committed the same UUID while we were saving.
        existing = get_attempt(attempt_id, token, db_engine)
        if existing is not None:
            return existing
        raise
    saved = get_attempt(attempt_id, token, db_engine)
    if saved is None:
        raise RuntimeError("The saved attempt could not be read back.")
    return saved


def history(token: str, db_engine=None) -> list[dict]:
    with Session(db_engine if db_engine is not None else engine) as session:
        user = session_user(session, token)
        rows = session.exec(select(Attempt).where(Attempt.user_id == user.id).order_by(Attempt.submitted_at.desc(), Attempt.id.desc())).all()
        return [attempt_data(row) for row in rows]


def summary(attempts: list[dict]) -> dict:
    """Average = arithmetic mean of attempt percentages, not pooled points."""
    if not attempts:
        return {"count": 0, "average": None, "best": None, "latest": None, "subjects": []}
    subjects = []
    names = dict(SUBJECTS)
    names.update({row["subject_id"]: row["subject_name"] for row in attempts})
    for subject_id, name in names.items():
        rows = [row for row in attempts if row["subject_id"] == subject_id]
        subjects.append({
            "name": name, "count": len(rows),
            "average": f"{sum(row['percentage'] for row in rows) / len(rows):.1f}%" if rows else "No attempts yet",
            "best": f"{max(row['percentage'] for row in rows):.1f}%" if rows else "No attempts yet",
        })
    return {
        "count": len(attempts),
        "average": sum(row["percentage"] for row in attempts) / len(attempts),
        "best": max(row["percentage"] for row in attempts),
        "latest": max(attempts, key=lambda row: row["submitted_at"])["date"],
        "subjects": subjects,
    }


if __name__ == "__main__":
    initialize()
    print(f"Database ready: {DB_PATH}")
