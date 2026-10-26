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
