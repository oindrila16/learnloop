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
        rx.text("Your score and explanations appear after you submit. Attempts are not saved yet."),
        rx.button("Start Quiz", on_click=Q.start, size="3"),
        rx.button("Return home", on_click=Q.home, variant="soft"),
        spacing="5", align="start",
    )


def option(item: rx.Var[dict[str, str]]) -> rx.Component:
    return rx.el.label(
        rx.hstack(
            rx.radio_group.item(value=item["id"]),
            rx.text(item["text"]),
            spacing="3", align="center",
        ),
        display="block", padding="16px", border="1px solid var(--gray-6)",
        border_radius="8px", cursor="pointer", width="100%",
    )


def quiz() -> rx.Component:
    return rx.vstack(
        rx.heading(Q.subject_name, as_="h1", size="6"),
        rx.text("Question ", Q.number, " of ", Q.total),
        rx.text(Q.answered, " of ", Q.total, " answered", color=rx.color("gray", 11)),
        rx.heading(Q.prompt, as_="h2", size="5"),
        rx.radio_group.root(
            rx.vstack(rx.foreach(Q.options, option), spacing="3", width="100%"),
            value=Q.selected_id,
            on_change=lambda value: Q.select_answer(Q.question_id, value),
            aria_label="Answer options", width="100%",
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
        rx.heading("Submit your quiz?", as_="h1", size="7"),
        rx.text("Unanswered questions: ", Q.total - Q.answered, " of ", Q.total, "."),
        rx.text("Unanswered questions earn zero points. Once submitted, your answers are final."),
        rx.flex(
            rx.button("Keep answering", on_click=Q.cancel_submit, variant="soft"),
            rx.button("Submit quiz", on_click=Q.submit), gap="16px", flex_wrap="wrap",
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
            rx.text(item["explanation"], color=rx.color("gray", 11)),
            align="start", spacing="3",
        ),
        width="100%", padding="20px",
    )


def results() -> rx.Component:
    return rx.vstack(
        rx.heading(Q.subject_name, " results", as_="h1", size="7"),
        rx.text(Q.score, " out of ", Q.total, " correct · ", Q.percentage, "%", size="6", weight="bold"),
        rx.flex(
            rx.button("Return home", on_click=Q.home, variant="soft"),
            rx.button("Start a fresh attempt", on_click=Q.start), gap="16px", flex_wrap="wrap",
        ),
        rx.foreach(Q.review, review_card),
        spacing="5", align="start", width="100%",
    )


def index() -> rx.Component:
    return rx.box(
        rx.container(
            rx.el.header(
                rx.hstack(
                    rx.icon("book-open", size=24, color=rx.color("indigo", 9)),
                    rx.text("LearnLoop", weight="bold", size="5"), align="center", spacing="3",
                ),
                padding_y="24px", border_bottom="1px solid var(--gray-5)",
            ),
            rx.el.main(
                rx.cond(Q.stage == "home", home(),
                    rx.cond(Q.stage == "intro", intro(),
                        rx.cond(Q.stage == "quiz", quiz(),
                            rx.cond(Q.stage == "confirm", confirmation(), results()),
                        ),
                    ),
                ),
                padding_y=rx.breakpoints(initial="32px", sm="56px"),
            ),
            rx.el.footer(rx.text("Learn at your own pace.", size="2"), padding_y="24px", border_top="1px solid var(--gray-5)"),
            size="4", padding_x=rx.breakpoints(initial="20px", sm="32px"),
        ),
        min_height="100vh", background=rx.color("gray", 2),
    )


app = rx.App()
app.add_page(index, route="/", on_load=Q.home, title="LearnLoop | Learn at your own pace", description="Practice Python, SQL, and Computer Fundamentals.")
