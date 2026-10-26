"""LearnLoop's home, quiz, and answer review screens."""

import reflex as rx

from .state import QuizState as Q


def subject_card(id: str, icon: str, title: str, description: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=26, color=rx.color("indigo", 9)),
            rx.heading(title, as_="h3", size="5"),
            rx.text(description, color=rx.color("gray", 11)),
            rx.button("Explore " + title, on_click=Q.choose_subject(id)),
            spacing="4",
            align="start",
        ),
        padding="24px",
        width="100%",
    )


def home() -> rx.Component:
    return rx.vstack(
        rx.heading("LearnLoop", as_="h1", size=rx.breakpoints(initial="8", sm="9")),
        rx.text("Build your confidence in Python, SQL, and computer fundamentals, one quiz at a time.", size="5", max_width="600px"),
        rx.heading("Explore the subjects", as_="h2", size="6"),
        rx.grid(
            subject_card("python", "code", "Python", "Practice variables, lists, functions, and basic expressions."),
            subject_card("sql", "database", "SQL", "Practice reading, filtering, and working with table data."),
            subject_card("computer-fundamentals", "monitor", "Computer Fundamentals", "Explore hardware, software, storage, and the basics of computers."),
            columns=rx.breakpoints(initial="1", sm="3"), spacing="5", width="100%",
        ),
        spacing="6", align="start", width="100%",
    )


def intro() -> rx.Component:
    return rx.vstack(
        rx.heading(Q.subject_name, as_="h1", size="7"),
        rx.text("Ten beginner questions, with four options each. Choose one answer per question."),
        rx.text("Move back and forth to change your answers, or leave questions unanswered. Each correct answer earns one point. There is no negative marking."),
        rx.text("Your score and explanations appear after you submit. Completed attempts are saved on this computer."),
        rx.button("Start Quiz", on_click=Q.start, size="3"),
        rx.button("Return home", on_click=Q.navigate("/"), variant="soft"),
        spacing="5", align="start",
    )


def option(item: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.el.label(
        rx.hstack(
            rx.radio_group.item(value=item["id"], id=item["id"], aria_labelledby=item["id"] + "-label"),
            rx.text(item["text"], id=item["id"] + "-label", flex="1", min_width="0"),
            rx.cond(Q.selected_id == item["id"], rx.text("Selected", size="2", weight="bold")),
            spacing="3", align="center",
        ),
        display="block", padding="18px", border="2px solid",
        border_color=rx.cond(Q.selected_id == item["id"], "var(--indigo-9)", "var(--gray-6)"),
        background=rx.cond(Q.selected_id == item["id"], "var(--indigo-3)", "white"),
        class_name="answer-row",
        border_radius="8px", cursor="pointer", width="100%",
    )


def quiz() -> rx.Component:
    return rx.vstack(
        rx.heading(Q.subject_name, as_="h1", size="6"),
        rx.text("Question ", Q.number, " of ", Q.total, role="status", aria_live="polite"),
        rx.text(Q.answered, " of ", Q.total, " answered", color=rx.color("gray", 11)),
        rx.text("Choose one answer. Use Tab to reach the options and arrow keys to move between them.", size="2", color=rx.color("gray", 11)),
        rx.heading(Q.prompt, as_="h2", size="5", id="question-heading", tab_index=-1, line_height="1.5"),
        rx.radio_group.root(
            rx.vstack(rx.foreach(Q.options, option), spacing="3", width="100%"),
            value=Q.selected_id,
            on_change=lambda value: Q.select_answer(Q.question_id, value),
            aria_labelledby="question-heading", width="100%", key=Q.question_id,
        ),
        rx.flex(
            rx.button("Previous", on_click=Q.previous, disabled=Q.number == 1, variant="soft"),
            rx.cond(Q.number < Q.total,
                rx.button("Next", on_click=Q.next),
                rx.button("Review submission", on_click=Q.request_submit),
            ),
            gap="16px", flex_wrap="wrap",
        ),
        spacing="5", align="start", width="100%",
    )


def confirmation() -> rx.Component:
    return rx.vstack(
        rx.heading("Submit your quiz?", as_="h1", size="7", id="confirmation-heading", tab_index=-1),
        rx.text("Unanswered questions: ", Q.total - Q.answered, " of ", Q.total, "."),
        rx.text("Unanswered questions earn zero points. Once submitted, your answers are final."),
        rx.cond(Q.saving, rx.text("Saving your quiz. Please wait…", role="status", aria_live="polite")),
        rx.flex(
            rx.button("Keep answering", on_click=Q.cancel_submit, variant="soft", disabled=Q.saving),
            rx.button(rx.cond(Q.saving, "Saving your quiz…", "Submit quiz"), on_click=Q.submit, disabled=Q.saving, aria_busy=Q.saving), gap="16px", flex_wrap="wrap",
        ),
        spacing="5", align="start",
    )


def review_card(item: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.badge(item["outcome"], variant="soft"),
            rx.heading(item["prompt"], as_="h2", size="4"),
            rx.text("Your answer: ", item["selected"]),
            rx.text("Correct answer: ", item["correct"], weight="bold"),
            rx.text("Options: ", item["options"], size="2"),
            rx.box(
                rx.text("Why this is correct", weight="bold", size="2"),
                rx.text(item["explanation"], color=rx.color("gray", 11)),
                border_top="1px solid var(--gray-5)", padding_top="12px", width="100%",
            ),
            align="start", spacing="3",
        ),
        width="100%", padding="20px",
    )


def results() -> rx.Component:
    return rx.vstack(
        rx.heading(Q.subject_name, " results", as_="h1", size="7", id="results-heading", tab_index=-1),
        rx.text(Q.score, " out of ", Q.total, " correct · ", Q.percentage, "%", size="6", weight="bold"),
        rx.text("Saved · ", Q.saved_date),
        rx.flex(
            rx.button("Return home", on_click=Q.navigate("/"), variant="soft"),
            rx.button("Start a fresh attempt", on_click=Q.start), gap="16px", flex_wrap="wrap",
        ),
        rx.button("View progress", on_click=Q.navigate("/progress"), variant="soft"),
        rx.foreach(Q.review, review_card),
        spacing="5", align="start", width="100%",
    )


def history_card(item: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(item["subject"], as_="h3", size="4"),
            rx.text(item["score"], " correct · ", item["percentage"]),
            rx.text(item["date"], size="2"),
            rx.button("View Results", on_click=Q.view_saved(item["id"]), variant="soft", disabled=Q.loading, aria_label="View results for " + item["subject"] + " on " + item["date"]),
            align="start", spacing="3",
        ), width="100%", padding="20px",
    )


def subject_summary(item: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(item["name"], as_="h3", size="4"),
            rx.text("Completed: ", item["count"]),
            rx.text("Average: ", item["average"]),
            rx.text("Best: ", item["best"]),
            align="start", spacing="3",
        ), width="100%",
    )


def progress() -> rx.Component:
    return rx.vstack(
        rx.heading("Your progress", as_="h1", size="7"),
        rx.text("Local single-user version · All completed quizzes on this computer."),
        rx.cond(Q.loading,
            rx.text("Loading your saved quizzes…", role="status"),
            rx.cond(~Q.history_error,
            rx.cond(Q.completed == 0,
                rx.text("No attempts yet. Complete a quiz to see your progress here."),
                rx.vstack(
                    rx.grid(
                        rx.card(rx.text("Completed quizzes"), rx.heading(Q.completed, size="6")),
                        rx.card(rx.text("Average percentage"), rx.heading(Q.average, size="6")),
                        rx.card(rx.text("Best percentage"), rx.heading(Q.best, size="6")),
                        columns=rx.breakpoints(initial="1", sm="3"), spacing="4", width="100%",
                    ),
                    rx.text("Latest attempt: ", Q.latest),
                    rx.text("Average is the arithmetic mean of completed-attempt percentages.", size="2"),
                    rx.heading("By subject", as_="h2", size="5"),
                    rx.grid(rx.foreach(Q.subject_summaries, subject_summary), columns=rx.breakpoints(initial="1", sm="3"), spacing="4", width="100%"),
                    rx.heading("Attempt history", as_="h2", size="5"),
                    rx.text("Newest first · Dates shown in UTC", size="2"),
                    rx.foreach(Q.history_items, history_card),
                    spacing="5", align="start", width="100%",
                ),
            ),
            rx.button("Retry loading history", on_click=Q.load_progress),
            ),
        ),
        rx.button("Return home", on_click=Q.navigate("/"), variant="soft"),
        spacing="5", align="start", width="100%",
    )


def discard_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Leave this quiz?"),
            rx.alert_dialog.description("Your unfinished answers will be discarded. Completed attempts stay saved."),
            rx.flex(
                rx.alert_dialog.cancel(rx.button("Keep answering", variant="soft")),
                rx.button("Discard and leave", on_click=Q.confirm_discard),
                gap="12px", flex_wrap="wrap", margin_top="24px",
            ), max_width="440px", width="calc(100vw - 40px)",
        ),
        open=Q.discard_open, on_open_change=Q.set_discard_open,
    )


def unavailable() -> rx.Component:
    return rx.vstack(
        rx.heading("Result unavailable", as_="h1", size="6"),
        rx.text("Open a saved attempt from Progress, or choose a subject to start a quiz."),
        rx.button("Open Progress", on_click=Q.navigate("/progress")),
        spacing="4", align="start",
    )


def index() -> rx.Component:
    return rx.box(
        rx.link("Skip to content", href="#main-content", class_name="skip-link"),
        discard_dialog(),
        rx.container(
            rx.el.header(
                rx.hstack(
                    rx.icon("book-open", size=24, color=rx.color("indigo", 9)),
                    rx.text("LearnLoop", weight="bold", size="5"), align="center", spacing="3",
                ),
                rx.badge("Local single-user version", variant="soft", margin_y="12px"),
                rx.el.nav(
                    rx.flex(
                        rx.button("Home", on_click=Q.navigate("/"), variant="soft", disabled=Q.saving | Q.loading),
                        rx.button("Progress", on_click=Q.navigate("/progress"), variant="soft", disabled=Q.saving | Q.loading),
                        gap="12px", flex_wrap="wrap",
                    ), aria_label="Main navigation",
                ),
                padding_y="24px", border_bottom="1px solid var(--gray-5)",
            ),
            rx.el.main(
                rx.cond(Q.error != "", rx.el.p(Q.error, role="alert", color=rx.color("red", 11))),
                rx.cond(Q.stage == "home", home(),
                    rx.cond(Q.stage == "intro", intro(),
                        rx.cond(Q.stage == "quiz", quiz(),
                            rx.cond(Q.stage == "confirm", confirmation(),
                                rx.cond(Q.stage == "progress", progress(),
                                    rx.cond((Q.stage == "results") & (Q.review.length() > 0), results(), unavailable()),
                                ),
                            ),
                        ),
                    ),
                ),
                id="main-content", tab_index=-1,
                max_width=rx.cond((Q.stage == "home") | (Q.stage == "progress"), "100%", "720px"),
                margin_x="auto", width="100%",
                padding_y=rx.breakpoints(initial="32px", sm="56px"),
            ),
            rx.el.footer(rx.text("Learn at your own pace.", size="2"), padding_y="24px", border_top="1px solid var(--gray-5)"),
            size="4", padding_x=rx.breakpoints(initial="20px", sm="32px"),
        ),
        min_height="100vh", background=rx.color("gray", 2),
    )


app = rx.App(stylesheets=["/styles.css"])
app.add_page(index, route="/", on_load=Q.home, title="LearnLoop | Learn at your own pace", description="Practice Python, SQL, and Computer Fundamentals.")
app.add_page(index, route="/progress", on_load=Q.load_progress, title="Progress | LearnLoop")

app.add_page(index, route="/results", on_load=Q.load_results, title="Results | LearnLoop")
