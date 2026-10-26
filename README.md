# LearnLoop

I'm building LearnLoop to practice Python and make a simple quiz app for Python,
SQL, and Computer Fundamentals. I'm using Reflex for the interface and app logic.

Each subject has ten beginner questions. You can move between questions, change
your answers, and leave questions unanswered. Before submitting, you'll see how
many you skipped. Correct answers earn one point; wrong or missing answers earn
zero. The results show your score and explain each answer.

This is a **local single-user version**, with no accounts. Completed quizzes are
saved in SQLite using SQLModel. The Progress page shows your history, average,
best score, and a summary for each subject. You can open any saved result again.
The average is the arithmetic mean of the percentages from completed attempts.

Only submitted quizzes are saved. Refreshing during a quiz returns you to the
home page, but your submitted attempts stay in the database. Different browser
sessions have separate active quizzes and share the same local history.

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
uv run python -m learnloop.database
uv run reflex run
```

Open http://localhost:3000. The first run needs an internet connection to download
some frontend tools and packages. Keep the terminal open while using the app,
and press Ctrl+C when you're done.

You can open progress directly at http://localhost:3000/progress.

## Database and backups

The database is `learnloop.db` in the project folder. It stays out of Git. The
initialization command creates missing tables and is safe to run again:

```sh
uv run python -m learnloop.database
```

It doesn't delete saved attempts. Run it before using the app for the first time.
If a save fails, the app shows an error and keeps your answers so you can retry.

Each saved attempt includes its own copy of the questions, options, answers, and
explanations. Editing the question bank won't change old results. Dates are
stored and displayed in UTC.

To back up your history, stop the app with Ctrl+C first, then copy the database
somewhere safe. For example, from the project folder:

```sh
cp learnloop.db "$HOME/Desktop/learnloop-backup.db"
```

Use a different backup filename if you want to keep earlier copies. To restore,
stop the app and copy your backup back to `learnloop.db`. Restoring replaces the
current history, so keep a copy of that file first.

## Where things are

- `learnloop/learnloop.py` has the home page, quiz screens, and results.
- `learnloop/state.py` handles answers, navigation, and submission on the server.
- `learnloop/questions.py` has the question bank, validation, and scoring.
- `learnloop/database.py` has the SQLite tables, saving, and history queries.
- `tests/test_quiz.py` checks the question bank and quiz flow.
- `tests/test_database.py` checks persistence using temporary databases.
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
