# LearnLoop

I'm building LearnLoop to practice Python and make a simple quiz app for Python,
SQL, and Computer Fundamentals. I'm using Reflex for the interface and app logic.

Each subject has ten beginner questions. You can move between questions, change
your answers, and leave questions unanswered. Before submitting, you'll see how
many you skipped. Correct answers earn one point; wrong or missing answers earn
zero. The results show your score and explain each answer.

Saved attempts and progress tracking will come later, using SQLite and SQLModel.
For now, attempts only last for the current session. Refreshing the page returns
you to the home page. This is still a local app for one person, with no accounts.

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

- `learnloop/learnloop.py` has the home page, quiz screens, and results.
- `learnloop/state.py` handles answers, navigation, and submission on the server.
- `learnloop/questions.py` has the question bank, validation, and scoring.
- `tests/test_quiz.py` checks the question bank and quiz flow.
- `rxconfig.py` has the Reflex settings.
- `uv.lock` keeps the dependency versions consistent.
- `AGENTS.md` has the project guidelines.

Reflex creates the `.web` folder automatically, so changes go in the Python files.

## Checking changes

```sh
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q learnloop rxconfig.py
uv run reflex run
```

After the app starts, open it in a browser and check it at both desktop and mobile
widths.

I'm following the [Reflex docs](https://reflex.dev/docs/getting-started/installation/)
as I build this.
