"""Re-exports app/agent/agent.py's public API at the `app.agent` package level.

Keeps every existing call site (`from app import agent; agent.ask(...)`,
`app/agent/__main__.py`'s `from app.agent import ask, ...`) working
unchanged, whether they're reaching into a single agent.py or, as here, a
package wrapping one.
"""
from app.agent.agent import (
    EventExplanation,
    EventExplanations,
    InterestsValidation,
    MATCH_EXPLANATION_PROMPT_TEMPLATE,
    ask,
    build_agent,
    explain_matches,
    search_festival_events,
    validate_interests,
)

__all__ = [
    "EventExplanation",
    "EventExplanations",
    "InterestsValidation",
    "MATCH_EXPLANATION_PROMPT_TEMPLATE",
    "ask",
    "build_agent",
    "explain_matches",
    "search_festival_events",
    "validate_interests",
]
