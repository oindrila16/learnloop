# LearnLoop

A beginner-friendly, local Python and Reflex learning app. Stage 1 includes a
light-themed home page and informational cards for Python, SQL, and Computer
Fundamentals. Cards are not interactive yet. Quizzes, results, saved attempts,
SQLite storage, and accounts are not implemented in this stage.

## Install and run

Requires macOS/Linux with curl (or install uv using the official instructions at
https://docs.astral.sh/uv/getting-started/installation/).

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal, then run:

```sh
cd /Users/oindrilasaha/Desktop/projects/learnloop
uv python install 3.12
uv sync --locked
uv run reflex run
```

Open http://localhost:3000 in your browser. Keep the terminal running; press
Ctrl+C to stop. The backend runs on port 8000. The first run downloads the
frontend build tools and packages and needs internet access. Reflex generates
its own frontend; there is no separate frontend to maintain.

Python is restricted to 3.12; `uv.lock` records exact dependency versions,
including Reflex 0.10.0. No database or Redis server is needed.

## Files

- `learnloop/learnloop.py`: the home page and reusable subject card.
- `rxconfig.py`: local app configuration.
- `AGENTS.md`: development rules for future stages.
- `pyproject.toml`, `.python-version`, `uv.lock`: reproducible Python environment.

The card grid uses one column below 768px and three columns at larger widths.
Do not edit `.web/`; Reflex generates it from Python.

## Check changes

```sh
uv run python -m compileall -q learnloop rxconfig.py
CI=1 uv run reflex run
```

Wait for compilation and the frontend/backend URLs. Open the page and check it
at desktop and mobile widths. A successful compile alone is not a browser test.

Reference: [installation](https://reflex.dev/docs/getting-started/installation/),
[core concepts](https://reflex.dev/docs/getting-started/basics/),
[state](https://reflex.dev/docs/state/overview/), and
[responsive styling](https://reflex.dev/docs/styling/responsive/).
