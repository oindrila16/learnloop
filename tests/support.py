"""Authenticated state fixtures. Only synthetic accounts in temporary databases."""

from reflex.istate.data import HeaderData

from learnloop.auth import issue_session, register
from learnloop.settings import COOKIE_NAME
from learnloop.state import QuizState


def new_account(username="learner"):
    user_id = register(username, "a long test password only")
    return user_id, issue_session(user_id)


def authenticated_state(token):
    state = QuizState(_reflex_internal_init=True)
    state.rx_router_headers = HeaderData(cookie=f"{COOKIE_NAME}={token}")
    state._sync_identity()
    return state
