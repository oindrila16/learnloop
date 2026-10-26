# LearnLoop

I'm building LearnLoop to practice Python and make a simple quiz app for Python,
SQL, and Computer Fundamentals. I'm using Reflex for the interface and app logic.

So far, it has a home page with three subject cards. The cards don't do anything
yet. Next, I plan to add multiple-choice quizzes, scores, and answer explanations.
Saved attempts and progress tracking will come later, using SQLite and SQLModel.
For now, this is a local app for one person.

## Run it locally

The project uses Python 3.12, Reflex 0.10.0, and uv.

If you don't have uv, install it first (macOS/Linux):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installing uv. Then, from the project folder, run:

```sh
uv python install 3.12
uv sync --locked
uv run reflex run
```

Open http://localhost:3000. The first run needs an internet connection to download
some frontend tools and packages. Keep the terminal open while using the app,
and press Ctrl+C when you're done.

## Where things are

- `learnloop/learnloop.py` has the home page and subject cards.
- `rxconfig.py` has the Reflex settings.
- `uv.lock` keeps the dependency versions consistent.
- `AGENTS.md` has the project guidelines.

Reflex creates the `.web` folder automatically, so changes go in the Python files.

## Checking changes

```sh
uv run python -m compileall -q learnloop rxconfig.py
uv run reflex run
```

After the app starts, open it in a browser and check it at both desktop and mobile
widths.

I'm following the [Reflex docs](https://reflex.dev/docs/getting-started/installation/)
as I build this.
