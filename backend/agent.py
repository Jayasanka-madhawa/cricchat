"""
Chat agent: RAG → generate SQL → execute → natural language answer.
"""

import json
from typing import Literal, TypedDict

from openai import OpenAI

from backend.config import OPENAI_API_KEY, OPENAI_MODEL
from backend.db import run_query
from backend.player_resolver import format_player_context, resolve_players
from backend.retriever import retrieve_context
from backend.sql_safety import validate_sql

MAX_HISTORY_MESSAGES = 10


class ChatMessage(TypedDict):
    role: str
    content: str

SQL_SYSTEM = """You are a PostgreSQL expert for cricket statistics.
Given schema context and examples, write ONE read-only SELECT query.
Rules:
- Use exact Cricsheet player names (e.g. V Kohli, JJ Bumrah, KC Sangakkara)
- Use deliveries table for ball-by-ball stats
- Column is batter (NOT batsman), bowler, runs_batter (NOT runs on one ball for centuries)
- Centuries / half-centuries: ALWAYS use a CTE — sum runs_batter per (match_id, innings_num), then COUNT innings WHERE runs >= 100
- NEVER put SUM() inside FILTER or WHERE on the same GROUP BY level (invalid in PostgreSQL)
- For total career runs use SUM(runs_batter) without GROUP BY; combine with centuries via a CTE, not one grouped SELECT
- When aggregating from a CTE, use the CTE column names (e.g. SUM(runs)), not deliveries columns
- Do NOT put WHERE runs >= 100 on the outer query when you also need total runs — use COUNT(*) FILTER (WHERE runs >= 100)
- Wides: COUNT with FILTER (WHERE NOT is_wide) for balls faced
- Career/overall stats (e.g. "Kohli strike rate in ODI") = NO over_num filter
- ONLY add over_num when the user asks for powerplay, first N overs, or death overs:
  - T20 powerplay / first 6 overs: over_num <= 5
  - ODI first 10 overs / PP1: over_num <= 9
  - T20 death (overs 17-20): over_num >= 15
- Match the closest example in context; prefer examples without over_num for general questions
- Player name lookup: SELECT player_name FROM players WHERE player_name ILIKE '%partial%';
- Kane Williamson = KS Williamson (not "Kane Williamson")
- Return ONLY the SQL query, no explanation
"""

ANSWER_SYSTEM = """You are a cricket stats assistant.
Given the user's question, the SQL used, and query results, answer clearly in plain English.
CRITICAL: Use ONLY numbers that appear in the Results JSON. NEVER invent, guess, or round beyond the data.
If results are empty, say no data was found. If the user asked for multiple stats but Results only has some, report only what is present.
If verifying data coverage for a player, state the Cricsheet name used and runs by format from Results.
Note: dataset covers Cricsheet matches mostly from 2003+; players debuting after 2003 should appear if the name is correct.
Keep answers concise (2-4 sentences)."""

INTENT_SYSTEM = """You route messages for CricChat, a cricket stats chatbot that looks up numbers from ball-by-ball SQL data.

Read the full conversation and classify the LATEST user message only.

STATS — the user wants a cricket statistic looked up from the database. Includes:
- genuine follow-ups to a prior stat question (e.g. "what about T20?" after Kohli ODI runs)
- disputes about missing data for a specific player ("why don't you have Kane data", "he debuted after 2010")
- requests to verify whether a player exists in the database

CHITCHAT — non-lookup messages only:
- greetings, introductions, thanks, bye
- general bot questions with no player/stat involved
- vague feedback with no player to look up ("that's wrong" with no context)
- off-topic chat or opinions

If CHITCHAT: write a brief natural reply (1-3 sentences). Do NOT invent cricket statistics.
If STATS: set reply to an empty string.

Return JSON only: {"intent": "STATS" or "CHITCHAT", "reply": "..."}"""

REWRITE_SYSTEM = """You rewrite follow-up cricket stat questions into one standalone question.
Use the conversation history to resolve pronouns, players, formats, and references.
Examples:
- "what about T20?" after Kohli ODI runs → "How many runs has Kohli scored in T20?"
- "show top 5" after most ODI runs → "Who are the top 5 ODI run scorers?"
- user disputes missing Kane data → "Show Kane Williamson runs by format using Cricsheet name KS Williamson"
- "why no data, he debuted after 2010" after Kane question → "Show KS Williamson total runs and balls by match_type"
Use exact Cricsheet player names from context (Kane Williamson = KS Williamson).
If the latest message is already a complete stat question on its own, return it unchanged.
Return ONLY the rewritten question, no explanation."""

DEFAULT_CHITCHAT_REPLY = (
    "I'm CricChat — ask me a cricket stats question and I'll look it up from match data. "
    'Try: "Kohli strike rate in ODI".'
)


def _client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not set. Copy backend/.env.example to .env and add your key."
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def _format_history(messages: list[ChatMessage]) -> str:
    lines = []
    for msg in messages:
        role = msg["role"].capitalize()
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def classify_messages(
    messages: list[ChatMessage],
) -> tuple[Literal["stats", "chitchat"], str]:
    """Decide whether to run SQL or reply conversationally."""
    if not messages:
        return "chitchat", DEFAULT_CHITCHAT_REPLY

    latest = messages[-1]["content"].strip()
    if not latest:
        return "chitchat", DEFAULT_CHITCHAT_REPLY

    history = messages[-MAX_HISTORY_MESSAGES:]
    client = _client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Conversation:\n{_format_history(history)}\n\n"
                    "Classify the latest user message:"
                ),
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    try:
        parsed = json.loads(response.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        return "stats", ""

    intent = str(parsed.get("intent", "STATS")).upper()
    reply = str(parsed.get("reply", "")).strip()
    if intent == "CHITCHAT":
        return "chitchat", reply or DEFAULT_CHITCHAT_REPLY
    return "stats", ""


def rewrite_question(messages: list[ChatMessage]) -> str:
    """Expand a follow-up into a standalone question using chat history."""
    if not messages:
        raise ValueError("At least one message is required.")
    latest = messages[-1]["content"].strip()
    if messages[-1]["role"] != "user":
        raise ValueError("The latest message must be from the user.")
    if len(messages) == 1:
        return latest

    history = messages[-MAX_HISTORY_MESSAGES:]
    client = _client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Conversation:\n{_format_history(history[:-1])}\n\n"
                    f"Latest user message: {latest}\n\n"
                    "Standalone question:"
                ),
            },
        ],
        temperature=0,
    )
    rewritten = (response.choices[0].message.content or "").strip()
    return rewritten or latest


def generate_sql(question: str, context: str, sql_error: str | None = None) -> str:
    client = _client()
    user_content = f"Context:\n{context}\n\nQuestion: {question}\n\nSQL:"
    if sql_error:
        user_content += (
            f"\n\nThe previous query failed with this database error:\n{sql_error}\n"
            "Write a corrected SELECT query:"
        )
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SQL_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )
    raw = response.choices[0].message.content or ""
    return validate_sql(raw)


def _run_sql_with_retry(
    question: str, context: str, max_retries: int = 2
) -> tuple[str, list[dict]]:
    sql = generate_sql(question, context)
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return sql, run_query(sql)
        except Exception as e:
            last_error = e
            if attempt >= max_retries:
                break
            sql = generate_sql(question, context, sql_error=str(e))
    raise last_error  # type: ignore[misc]


def format_answer(question: str, sql: str, rows: list[dict]) -> str:
    client = _client()
    data = json.dumps(rows[:20], default=str)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"SQL:\n{sql}\n\n"
                    f"Results:\n{data}"
                ),
            },
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or "No answer generated."


def ask(question: str) -> dict:
    """Single-turn pipeline: retrieve → SQL → execute → answer."""
    return ask_with_messages([{"role": "user", "content": question}])


def ask_with_messages(messages: list[ChatMessage]) -> dict:
    """
    Multi-turn pipeline: rewrite follow-up → retrieve → SQL → execute → answer.

    Returns dict with answer, sql, rows, and context preview.
    """
    latest = messages[-1]["content"].strip()
    intent, chitchat_reply = classify_messages(messages)
    if intent == "chitchat":
        return {
            "question": latest,
            "answer": chitchat_reply,
            "sql": "",
            "rows": [],
            "context_preview": "",
        }

    question = rewrite_question(messages)
    rag_context = retrieve_context(question)
    player_names = resolve_players(question)
    player_context = format_player_context(player_names)
    context = (
        f"{player_context}\n\n---\n\n{rag_context}"
        if player_context
        else rag_context
    )
    sql, rows = _run_sql_with_retry(question, context)
    answer = format_answer(question, sql, rows)

    return {
        "question": question,
        "answer": answer,
        "sql": sql,
        "rows": rows,
        "context_preview": context[:500] + ("..." if len(context) > 500 else ""),
    }
