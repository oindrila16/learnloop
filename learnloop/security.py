"""Clear cached private state before hydration and after session invalidation."""

from dataclasses import replace

from reflex.middleware import Middleware

from .state import QuizState


class SessionBoundary(Middleware):
    async def preprocess(self, app, state, event):
        quiz = await state.get_state(QuizState)
        quiz._sync_identity()
        # Hydration must run only after the previous account's data is cleared.
        return None

    async def postprocess(self, app, state, event, update):
        quiz = await state.get_state(QuizState)
        identity = quiz._identity_session
        quiz._sync_identity()
        if identity != quiz._identity_session:
            return replace(update, delta=state.dict(), events=[])
        return update
