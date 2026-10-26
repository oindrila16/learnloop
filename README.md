# LearnLoop

LearnLoop is a simple quiz app for Python, SQL and Computer Fundamentals.
I'm building this project to practice Python and learn Reflex.

Each subject has 10 questions. You can go back, change your answers or skip a
question. A correct answer gets 1 point. Wrong or skipped answers get 0. After
submitting, you can see your score and an explanation for each answer.

You can make an account and keep your quiz history private. The Progress page
shows your old quizzes, average score and best score. The average is the mean of
your completed quiz percentages.

## What you need

The project uses Python 3.12, Reflex 0.10.0, SQLite, SQLModel and pwdlib for
password hashing. uv installs Python and the project packages. You don't need to
install a separate database server or frontend.

On macOS or Linux, install uv from its official installer:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
uv python install 3.12
```

You can also follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
If you open a new terminal and uv isn't found, run the `source` command again.

## Download the project

On a Mac, `git --version` will tell you if Git is available. macOS may prompt you
to install its command-line tools if it isn't.

If you haven't downloaded the project yet, run:

```sh
git clone https://github.com/oindrila16/learnloop.git
cd learnloop
```

If you already have the project, just open a terminal in its folder. Then install
the packages using the versions in `uv.lock`:

```sh
uv sync --locked
```

You don't need to activate `.venv` yourself when using `uv run`.

## Set up or update the database

Run this from the project folder:

```sh
uv run python -m learnloop.database
```

This creates `learnloop.db` if needed. For an existing database, it adds the
tables and fields needed for accounts without deleting saved quizzes. Running it
again is safe. Stop the app and back up an existing database before updating it.

Quizzes saved before accounts were added are still in the database. They won't
appear in a new account's history because they don't belong to that account.

## Run the app

```sh
uv run reflex run --backend-host 127.0.0.1
```

Open http://localhost:3000 and register or log in. Use `localhost` consistently
rather than switching to `127.0.0.1` in the browser. The first run needs internet
to download frontend tools and packages.

Keep the terminal running while using the app. Press Ctrl+C to stop. If an older
version is running, stop it before starting this one. Ports 3000 and 8000 should
be free. If Reflex chooses other ports automatically, the login addresses won't
match. See [AUTH.md](AUTH.md) to configure different ports deliberately.

Use Tab to move between controls and arrow keys to choose an answer. Home and
Progress ask before leaving an unfinished quiz. Only submitted attempts are
saved. Refreshing can clear an unfinished quiz; completed attempts stay saved.

## Run the checks

```sh
uv run python -m unittest discover -s tests -v
uv run reflex compile --dry
```

The tests use temporary databases and leave your saved quizzes alone. They cover
scoring, answer navigation, persistence after restart, duplicate submissions,
failed saves, accounts and private history. The compile command checks the
Reflex pages without starting a server. You still need to open the app to check
how the pages look and work in a browser.

## Add or edit questions

Edit `learnloop/questions.py`. The subjects are `python`, `sql` and
`computer-fundamentals`. Each subject currently needs exactly 10 questions, so
replace an existing entry when adding a new one.

An entry looks like this:

```python
question(
    "py-11",
    "Which value is a Python Boolean?",
    ("'True'", "True", "3.5", "[]"),
    1,
    "True is a Boolean. Quotes would make it a string.",
),
```

The number `1` means the second option is correct. The choices are numbered
0, 1, 2 and 3 in this file. Write four different options, with no blank answers, and choose one
correct option. Give every new question a unique ID and a short explanation.
Option IDs are made from the question ID and the letters a–d.

For wording fixes, keep the existing ID and option order. Use original questions
with clear answers. State the context if the answer depends on a language version
or SQL dialect. Saved results keep their original question and answer snapshots.

Validate the bank after editing it, then run the tests:

```sh
uv run python -c "from learnloop.questions import validate_bank; validate_bank(); print('Question bank is valid')"
uv run python -m unittest discover -s tests -v
```

Invalid entries raise an error instead of silently starting a broken quiz.

## Back up your history

Stop every running copy of the app first. Then copy the database somewhere safe:

```sh
cp learnloop.db "$HOME/Desktop/learnloop-backup.db"
```

Choose a new filename to keep older backups. To restore one, stop the app and
copy the backup back as `learnloop.db`. Keep a copy of the current database first,
because restoring replaces it. Backups contain private history, password hashes
and session hashes, so keep them private.

## Current limits

- There is no email verification, password recovery, social login or MFA.
- Login lasts up to eight hours. Logging out ends that session on the server.
- Too many login tries can block further tries for up to 15 minutes.
- Refreshing can discard an unfinished quiz. There are no saved drafts.
- History dates are shown in UTC.
- An idle tab may show previously loaded data after logout in another tab. Its
  next server interaction checks the session and clears private data.
- This is a small SQLite app. It needs HTTPS, hosting configuration and a security
  review before public use. Local login working doesn't make it production-ready.

See [AUTH.md](AUTH.md) for cookie settings, migration details and HTTPS setup.
