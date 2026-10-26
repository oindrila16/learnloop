"""Local Reflex configuration."""

import reflex as rx
from learnloop.settings import APP_ORIGIN, BACKEND_ORIGIN

config = rx.Config(
    app_name="learnloop",
    api_url=BACKEND_ORIGIN,
    deploy_url=APP_ORIGIN,
    cors_allowed_origins=[APP_ORIGIN],
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="light", accent_color="indigo", radius="large"),
        ),
    ],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
