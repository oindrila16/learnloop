"""The trusted question bank. Correct answers stay on the server until submission."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    options: tuple[tuple[str, str], ...]
    correct_id: str
    explanation: str


def question(id: str, prompt: str, options: tuple[str, str, str, str], correct: int, explanation: str) -> Question:
    """Give each option a stable ID based on its question ID."""
    if len(options) != 4 or type(correct) is not int or not 0 <= correct < 4:
        raise ValueError(f"{id}: provide four options and a correct index from 0 to 3.")
    return Question(id, prompt, tuple((f"{id}-{letter}", text) for letter, text in zip("abcd", options)), f"{id}-{'abcd'[correct]}", explanation)


SUBJECTS = {
    "python": "Python",
    "sql": "SQL",
    "computer-fundamentals": "Computer Fundamentals",
}

BANK = {
    "python": (
        question("py-01", "In Python 3, what is the value of 3 + 4 * 2?", ("14", "11", "10", "9"), 1, "Multiplication happens before addition, so 3 + 8 is 11."),
        question("py-02", "Which value is a string in Python?", ('"42"', "42", "4.2", "True"), 0, "Quotes make \"42\" a string, even though its characters are digits."),
        question("py-03", "What does len([10, 20, 30]) return?", ("2", "60", "3", "30"), 2, "len returns the number of items; this list contains three items."),
        question("py-04", "If colors = ['red', 'blue'], what is colors[0]?", ("blue", "0", "colors", "red"), 3, "Python sequences start indexing at zero, so index 0 holds 'red'."),
        question("py-05", "Which keyword begins a function definition in Python?", ("function", "def", "make", "func"), 1, "The def keyword introduces a function definition."),
        question("py-06", "What is the value of 7 // 2 in Python 3?", ("3", "3.5", "4", "1"), 0, "Floor division rounds the quotient down; 7 divided by 2 gives 3 after flooring."),
        question("py-07", "Which expression checks whether x equals 5?", ("x = 5", "x != 5", "x == 5", "x > 5"), 2, "== compares values for equality. A single = assigns a value."),
        question("py-08", "What does items.append('book') do to a list named items?", ("Removes its first item", "Sorts the list", "Replaces every item", "Adds 'book' at the end"), 3, "append adds one item to the end of an existing list."),
        question("py-09", "Which line starts a comment in Python?", ("# a note", "// a note", "<!-- a note -->", "/* a note */"), 0, "Outside a string, # starts a comment that runs to the end of the line."),
        question("py-10", "What is the value of bool([]) in Python?", ("True", "False", "None", "An empty string"), 1, "An empty list is false when converted to a Boolean."),
    ),
    "sql": (
        question("sql-01", "Which SQL statement reads rows from a table?", ("DELETE", "INSERT", "SELECT", "UPDATE"), 2, "SELECT retrieves data from tables or other query sources."),
        question("sql-02", "Which clause filters individual rows in a SELECT query?", ("WHERE", "ORDER BY", "GROUP BY", "FROM"), 0, "WHERE keeps rows for which its condition is true."),
        question("sql-03", "Which query reads only the name column from students?", ("SELECT students FROM name;", "SELECT * FROM students;", "DELETE name FROM students;", "SELECT name FROM students;"), 3, "The SELECT list names the columns to retrieve; FROM names the table."),
        question("sql-04", "What does ORDER BY age ASC request?", ("Largest ages first", "Smallest ages first", "Only unique ages", "Only missing ages"), 1, "ASC requests ascending order, so smaller numeric ages come first."),
        question("sql-05", "Which condition checks for a missing email value in SQL?", ("email = NULL", "email == NULL", "email IS NULL", "email IS EMPTY"), 2, "IS NULL tests for a NULL value. Ordinary equality does not test for NULL."),
        question("sql-06", "What does COUNT(*) count in a query without GROUP BY?", ("All rows in the query result before aggregation", "Only non-NULL values in the first column", "The number of columns", "Only distinct rows"), 0, "COUNT(*) counts every input row, including rows with NULL column values."),
        question("sql-07", "Which SQL statement adds a new row to a table?", ("SELECT", "UPDATE", "DELETE", "INSERT"), 3, "INSERT adds rows to a table."),
        question("sql-08", "Which SQL statement changes values in existing rows?", ("INSERT", "UPDATE", "SELECT", "CREATE TABLE"), 1, "UPDATE changes column values in existing rows."),
        question("sql-09", "What does SELECT DISTINCT city FROM students do?", ("Deletes repeated cities", "Sorts cities alphabetically", "Returns each city value once", "Counts students in each city"), 2, "DISTINCT removes duplicate values from the query output; it does not change stored rows."),
        question("sql-10", "Which operator requires both conditions to be true?", ("AND", "OR", "NOT", "LIKE"), 0, "AND is true when both of its conditions are true."),
    ),
    "computer-fundamentals": (
        question("cf-01", "Which component executes program instructions?", ("Monitor", "CPU", "Keyboard", "Printer"), 1, "The central processing unit executes program instructions."),
        question("cf-02", "Which type of memory normally loses its contents when power is turned off?", ("SSD", "Hard disk", "DVD", "RAM"), 3, "RAM is volatile working memory and normally needs power to retain its contents."),
        question("cf-03", "What is an operating system's main role?", ("Manage hardware and provide services for programs", "Print every file", "Replace all applications", "Supply electrical power"), 0, "An operating system manages resources such as memory, files, and devices for programs."),
        question("cf-04", "How many bits are in one byte?", ("2", "4", "8", "16"), 2, "A byte consists of eight bits."),
        question("cf-05", "Which device is primarily used to enter text?", ("Speaker", "Keyboard", "Monitor", "Projector"), 1, "A keyboard is an input device commonly used to enter text."),
        question("cf-06", "Which is an example of application software?", ("A memory chip", "A power supply", "A processor", "A spreadsheet program"), 3, "A spreadsheet is software used to perform a user task; the other choices are hardware."),
        question("cf-07", "What is a backup?", ("A separate copy kept to help recover data", "A faster processor", "A type of keyboard", "An empty folder"), 0, "A backup is a separate copy of data that can help restore lost or damaged files."),
        question("cf-08", "Which digits are used in the binary number system?", ("1 and 2", "0 through 9", "0 and 1", "A through F"), 2, "Binary is base two and uses only the digits 0 and 1."),
        question("cf-09", "What is the main purpose of a web browser?", ("Provide power to a computer", "Retrieve and display web pages", "Replace physical storage", "Cool the processor"), 1, "A browser retrieves web content and displays pages for the user."),
        question("cf-10", "Which device normally keeps saved files after the computer is shut down?", ("CPU register", "RAM module", "CPU cache", "SSD"), 3, "An SSD is nonvolatile storage, so it retains saved data without power."),
    ),
}


def validate_bank(bank=BANK, subjects=SUBJECTS) -> None:
    """Fail at startup rather than silently serving a broken question bank."""
    if set(bank) != set(subjects) or len(subjects) != 3:
        raise ValueError("The bank must match the three subject IDs.")
    seen = set(subjects)
    for questions in bank.values():
        if len(questions) != 10:
            raise ValueError("Each subject needs ten questions.")
        for item in questions:
            ids = [item.id, *(option_id for option_id, _ in item.options)]
            if any(not isinstance(id, str) or not id.strip() or id in seen for id in ids) or len(set(ids)) != len(ids):
                raise ValueError("Question and option IDs must be unique and nonempty.")
            seen.update(ids)
            texts = [text for _, text in item.options]
            if len(texts) != 4 or any(not isinstance(text, str) or not text.strip() for text in texts) or len({text.strip() for text in texts}) != 4:
                raise ValueError("Each question needs four distinct options.")
            if item.correct_id not in dict(item.options):
                raise ValueError("Correct option must belong to the question.")
            if not item.prompt.strip() or not item.explanation.strip():
                raise ValueError("Questions need a prompt and explanation.")


def grade(subject_id: str, answers: dict[str, str]) -> tuple[int, list[dict[str, str]]]:
    """Score only trusted IDs. Build the review only when the server submits."""
    questions = BANK[subject_id]
    allowed = {q.id: dict(q.options) for q in questions}
    if any(qid not in allowed or oid not in allowed[qid] for qid, oid in answers.items()):
        raise ValueError("Unknown question or option ID.")
    score = 0
    review = []
    for q in questions:
        selected = answers.get(q.id)
        correct = selected == q.correct_id
        score += int(correct)
        options = dict(q.options)
        review.append({"id": q.id, "prompt": q.prompt, "selected": options.get(selected, "Not answered"), "correct": options[q.correct_id], "explanation": q.explanation, "outcome": "Correct" if correct else "Incorrect"})
    return score, review


validate_bank()
