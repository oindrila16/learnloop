"""LearnLoop's home page. Quiz interactions will be added in a later stage."""

import reflex as rx


def subject_card(icon: str, title: str, description: str) -> rx.Component:
    """One informational subject card; its arguments are ordinary Python strings."""
    return rx.card(
        rx.vstack(
            rx.box(
                rx.icon(icon, size=26, color=rx.color("indigo", 9)),
                padding="12px",
                background=rx.color("indigo", 3),
                border_radius="12px",
            ),
            rx.heading(title, as_="h3", size="5"),
            rx.text(description, color=rx.color("gray", 11), size="3"),
            rx.badge("Quizzes coming soon", variant="soft"),
            spacing="4",
            align="start",
        ),
        padding="24px",
        width="100%",
    )


def index() -> rx.Component:
    """A responsive, static introduction to the three learning subjects."""
    return rx.box(
        rx.container(
            rx.hstack(
                rx.icon("book-open", size=24, color=rx.color("indigo", 9)),
                rx.text("LearnLoop", weight="bold", size="5"),
                spacing="3",
                align="center",
                padding_y="24px",
                border_bottom="1px solid var(--gray-5)",
            ),
            rx.el.main(
                rx.vstack(
                    rx.badge("A little learning, every day", variant="soft", size="2"),
                    rx.heading(
                        "LearnLoop",
                        as_="h1",
                        size=rx.breakpoints(initial="8", sm="9"),
                    ),
                    rx.text(
                        "Build your confidence in Python, SQL, and computer fundamentals, "
                        "one quiz at a time.",
                        size="5",
                        color=rx.color("gray", 11),
                        max_width="600px",
                    ),
                    spacing="5",
                    align="start",
                    padding_y=rx.breakpoints(initial="40px", sm="64px"),
                ),
                rx.vstack(
                    rx.heading("Explore the subjects", as_="h2", size="6"),
                    rx.text(
                        "Three places to start. Quizzes will be available in the next stage.",
                        color=rx.color("gray", 11),
                    ),
                    rx.grid(
                        subject_card("code", "Python", "Get comfortable with variables, loops, functions, and the basics of programming."),
                        subject_card("database", "SQL", "Learn how to select, filter, and organize data with clear, practical queries."),
                        subject_card("monitor", "Computer Fundamentals", "Understand hardware, software, operating systems, and how computers work."),
                        columns=rx.breakpoints(initial="1", sm="3"),
                        spacing="5",
                        width="100%",
                    ),
                    spacing="5",
                    align="start",
                    width="100%",
                ),
                padding_bottom="48px",
            ),
            rx.el.footer(
                rx.text("Learn at your own pace.", size="2", color=rx.color("gray", 11)),
                padding_y="24px",
                border_top="1px solid var(--gray-5)",
            ),
            size="4",
            padding_x=rx.breakpoints(initial="20px", sm="32px"),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )


app = rx.App()
app.add_page(index, route="/", title="LearnLoop | Learn at your own pace", description="Build confidence in Python, SQL, and Computer Fundamentals.")
