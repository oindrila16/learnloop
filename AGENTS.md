# LearnLoop project instructions

- Keep this a beginner-friendly Python and Reflex app; implement only the requested stage.
- Consult current official documentation and check the installed Reflex version rather than guessing APIs.
- Use `rx.cond` and `rx.foreach` for dynamic state-dependent rendering. Never use ordinary Python `if`, `for`, `len`, or f-strings on Reflex state Vars inside component rendering.
- Mutate application state through event handlers.
- Keep database objects and correct-answer data out of browser-visible quiz state.
- When persistence is requested, use SQLite and SQLModel directly (`SQLModel`, `create_engine`, and `Session`), not the legacy Reflex ORM.
- Do not edit generated `.web` files.
- Keep generated files, secrets, databases, and virtual environments out of Git. Track `uv.lock`.
- Use uv for dependencies and commands. Keep dependencies and file structure small.
- Run relevant checks after each stage. Never claim a browser test passed unless it was actually performed.
- Do not add accounts until a later requested stage.
- Keep project writing natural, simple, and personal. The README should sound like the owner's own project notes, without inflated claims or invented experience.
- This is a local single-user app: active quizzes are session-specific, but saved history is shared locally.
- Initialize SQLite explicitly with `uv run python -m learnloop.database`. Never delete or recreate it automatically.
- Save submissions and answer snapshots in one transaction; preserve the unique server-generated attempt ID when retrying failed saves.
- Store submission timestamps in UTC and load historical reviews from saved snapshots, not the current question bank.
- Persistence tests must use temporary databases and leave personal quiz history untouched.
