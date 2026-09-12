"""LLM agent chaining an OpenAI chat model with the RAG retrieval in ranking.py.

A LangChain tool-calling agent: it can search the festival event catalog
through a tool wrapping `ranking.semantic_search()`, then answer in natural
language grounded in whatever that search actually returns. This is the
"agent" side of the app -- ranking.py's `generate_recommendations` powers
the swipe deck directly; this module is for anything conversational (a
chat interface, a "why did you recommend this" explainer, etc.) built on
top of the same retrieval.

Requires OPENAI_API_KEY in the environment (read automatically by
langchain-openai). Configure the model via OPENAI_AGENT_MODEL if the
default isn't available on your account.
"""
from __future__ import annotations

import os

from langchain.agents import create_agent
from langchain_core.tools import tool

from app import store
from app.ranking import semantic_search

_MODEL = os.environ.get("OPENAI_AGENT_MODEL", "openai:gpt-4o-mini")

_SYSTEM_PROMPT = (
    "You are a helpful assistant for the Ars Electronica Festival 2026 "
    '("Negotiating Humanity") in Linz, Austria. Use the search_festival_events '
    "tool to find real events before recommending anything -- never invent an "
    "event, time, or venue. Ground every recommendation in what the tool "
    "actually returns: mention the event's title and time, and say so "
    "plainly if nothing in the catalog fits what the user asked for."
)


@tool
def search_festival_events(query: str, top_k: int = 5) -> str:
    """Search the Ars Electronica Festival 2026 event catalog for events
    semantically related to `query`. Returns up to `top_k` matches, each
    with its id, title, category, date/time, and venue."""
    events = semantic_search(query, store.get_events(), top_k=top_k)
    if not events:
        return "No matching events found."
    return "\n".join(
        f"- [{e['id']}] {e['title']} ({e['category']}) -- {e['time']} "
        f"@ {e['location']['venue']}"
        for e in events
    )


def build_agent():
    """Construct the tool-calling agent. Cheap (no API call happens until
    it's invoked) but still worth building once -- see `_AGENT` below."""
    return create_agent(_MODEL, tools=[search_festival_events], system_prompt=_SYSTEM_PROMPT)


_AGENT = build_agent()

def ask(question: str, history: list[dict] | None = None) -> str:
    """Ask the agent a question, optionally continuing a prior conversation.

    `history` is a list of `{"role": "user" | "assistant", "content": str}`
    dicts from earlier turns -- pass back what you got from a previous
    `ask()` call's messages if you want multi-turn context; omit it for a
    one-shot question.
    """
    messages = [*(history or []), {"role": "user", "content": question}]
    result = _AGENT.invoke({"messages": messages})
    return result["messages"][-1].content


if __name__ == "__main__":
    # Quick manual smoke test: `python -m app.agent` from backend/.
    print(ask("I have tonight free and love hands-on, playful stuff. Any ideas?"))
