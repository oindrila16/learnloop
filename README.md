# LearnLoop

LearnLoop is a simple quiz app for Python, SQL and Computer Fundamentals.
I'm building this project to practice Python and learn Reflex.

Each subject has 10 questions. You can go back, change your answers or skip a
question. After submitting, you can see your score, the correct answers and a
short explanation for each question.

The Progress page shows your saved quizzes, average score and best score. You
can also open your old results from there. The average is calculated from each
completed quiz's percentage.

This is a local single-user app. There are no accounts yet.

## What I used

- Python 3.12
- Reflex for the pages and app logic
- SQLite and SQLModel to save quiz attempts
- uv to manage packages

## How to run

First, install uv if you don't have it. On macOS or Linux:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

Check that it works:

```sh
uv --version
```

Clone the project and open its folder:

```sh
git clone https://github.com/oindrila16/learnloop.git
cd learnloop
```

If you already have the project, just open a terminal in the project folder.
Then run:

```sh
uv python install 3.12
uv sync --locked
uv run python -m learnloop.database
uv run reflex run
```

Open http://localhost:3000 in your browser. The first run needs internet to
download the required tools and packages. Keep the terminal running while using
the app. Press Ctrl+C to stop it.

## A few things to know

- A correct answer gets 1 point. A wrong or skipped answer gets 0.
- Only submitted quizzes are saved.
- Refreshing the page can clear an unfinished quiz. Saved quizzes stay there.
- Home and Progress ask before you leave an unfinished quiz.
- You can use Tab to move between controls and arrow keys to choose an answer.
- Dates in the history are shown in UTC.

## Saved data

Quiz history is stored in `learnloop.db` in the project folder. This file is not
uploaded to GitHub. Running the database setup command again keeps your history.
Old results keep their own copy of the questions and answers, so changing a
question later won't change a saved result.

To make a backup, stop the app first. Then copy the database somewhere safe:

```sh
cp learnloop.db "$HOME/Desktop/learnloop-backup.db"
```

Use a new filename if you want to keep an older backup. To restore a backup, stop
the app and copy it back as `learnloop.db`. Keep a copy of your current database
first, because restoring replaces it.

## Tests

Run the tests from the project folder:

```sh
uv run python -m unittest discover -s tests -v
```

The tests use temporary databases, so they don't change your saved quizzes.
