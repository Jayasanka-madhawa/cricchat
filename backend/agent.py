"""
Chat agent: RAG → generate SQL → execute → natural language answer.
"""

import json

from openai import OpenAI

from backend.config import OPENAI_API_KEY, OPENAI_MODEL
from backend.db import run_query
from backend.retriever import retrieve_context
from backend.sql_safety import validate_sql

SQL_SYSTEM = """You are a PostgreSQL expert for cricket statistics.
Given schema context and examples, write ONE read-only SELECT query.
Rules:
- Use exact Cricsheet player names (e.g. V Kohli, JJ Bumrah, KC Sangakkara)
- Use deliveries table for ball-by-ball stats
- Column is batter (NOT batsman), bowler, runs_batter (NOT runs on one ball for centuries)
- Centuries: SUM(runs_batter) per innings (match_id, innings_num), COUNT where total >= 100
- Wides: COUNT with FILTER (WHERE NOT is_wide) for balls faced
- Career/overall stats (e.g. "Kohli strike rate in ODI") = NO over_num filter
- ONLY add over_num when the user asks for powerplay, first N overs, or death overs:
  - T20 powerplay / first 6 overs: over_num <= 5
  - ODI first 10 overs / PP1: over_num <= 9
  - T20 death (overs 17-20): over_num >= 15
- Match the closest example in context; prefer examples without over_num for general questions
- Return ONLY the SQL query, no explanation
"""

ANSWER_SYSTEM = """You are a cricket stats assistant.
Given the user's question, the SQL used, and query results, answer clearly in plain English.
Include specific numbers. If results are empty, say no data was found.
Keep answers concise (2-4 sentences)."""


def _client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not set. Copy backend/.env.example to .env and add your key."
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_sql(question: str, context: str) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SQL_SYSTEM},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}\n\nSQL:",
            },
        ],
        temperature=0,
    )
    raw = response.choices[0].message.content or ""
    return validate_sql(raw)


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
    """
    Full pipeline: retrieve → SQL → execute → answer.

    Returns dict with answer, sql, rows, and context preview.
    """
    context = retrieve_context(question)
    sql = generate_sql(question, context)
    rows = run_query(sql)
    answer = format_answer(question, sql, rows)

    return {
        "question": question,
        "answer": answer,
        "sql": sql,
        "rows": rows,
        "context_preview": context[:500] + ("..." if len(context) > 500 else ""),
    }
