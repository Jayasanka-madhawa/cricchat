"""Resolve user player names to exact Cricsheet names before SQL generation."""

import re
from pathlib import Path

from sqlalchemy import create_engine, text

from backend.config import DATABASE_URL, ROOT

ALIASES_PATH = ROOT / "rag" / "knowledge" / "player_aliases.md"

STOPWORDS = {
    "about", "after", "against", "all", "and", "any", "are", "average", "balls",
    "batting", "bowler", "bowling", "career", "centuries", "century", "compare",
    "data", "death", "debut", "does", "economy", "first", "format", "from",
    "have", "highest", "how", "many", "match", "most", "name", "overs",
    "partnership", "played", "player", "powerplay", "rate", "runs", "score",
    "scored", "show", "since", "strike", "that", "the", "their", "total",
    "what", "when", "which", "who", "why", "wickets", "with", "you", "your",
    "odi", "t20", "test", "ipl", "bbl", "psl", "mdm", "odm",
}

_TOKEN_RE = re.compile(r"[a-z][a-z'-]{1,}")


def _load_aliases() -> dict[str, str]:
    if not ALIASES_PATH.exists():
        return {}
    aliases: dict[str, str] = {}
    for line in ALIASES_PATH.read_text().splitlines():
        if "→" not in line or line.strip().startswith("#"):
            continue
        left, right = line.split("→", 1)
        key = left.strip().lower()
        value = right.strip()
        if key and value:
            aliases[key] = value
    return aliases


def _match_aliases(question: str, aliases: dict[str, str]) -> list[str]:
    q = question.lower()
    found: list[str] = []
    seen: set[str] = set()
    for alias in sorted(aliases, key=len, reverse=True):
        if alias in q:
            name = aliases[alias]
            if name not in seen:
                seen.add(name)
                found.append(name)
    return found


def _search_terms(question: str) -> list[str]:
    tokens = [
        t
        for t in _TOKEN_RE.findall(question.lower())
        if t not in STOPWORDS and len(t) >= 3
    ]
    terms: list[str] = []
    for n in (3, 2, 1):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i : i + n])
            if phrase not in terms:
                terms.append(phrase)
    return terms


def _lookup_in_db(term: str, limit: int = 5) -> list[str]:
    if not re.fullmatch(r"[a-z][a-z' -]*", term):
        return []

    tokens = term.split()
    if not tokens:
        return []
    if len(tokens) == 1 and len(tokens[0]) < 5:
        return []

    conditions = " AND ".join(
        f"player_name ILIKE :t{i}" for i in range(len(tokens))
    )
    params = {f"t{i}": f"%{tok}%" for i, tok in enumerate(tokens)}
    exact = term.title() if len(tokens) > 1 else tokens[0].title()
    sql = f"""
        SELECT player_name
        FROM players
        WHERE {conditions}
        ORDER BY
            CASE WHEN lower(player_name) = lower(:exact) THEN 0 ELSE 1 END,
            length(player_name)
        LIMIT :lim
    """
    params["exact"] = exact
    params["lim"] = limit

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        return [row[0] for row in result]


def resolve_players(question: str, max_names: int = 5) -> list[str]:
    """
    Map natural language player references to Cricsheet player_name values.

    1. Static aliases from rag/knowledge/player_aliases.md
    2. PostgreSQL players table (ILIKE on name tokens)
    """
    aliases = _load_aliases()
    resolved = _match_aliases(question, aliases)
    seen = set(resolved)
    has_alias = bool(resolved)

    if len(resolved) < max_names:
        for term in _search_terms(question):
            if len(resolved) >= max_names:
                break
            if has_alias and len(term.split()) == 1:
                continue
            matches = _lookup_in_db(term)
            if not matches:
                continue
            for name in matches:
                if name not in seen:
                    seen.add(name)
                    resolved.append(name)
            # A multi-word DB hit is usually the right player — avoid noisier single-token matches
            if len(term.split()) >= 2 and matches:
                break

    return resolved[:max_names]


def format_player_context(names: list[str]) -> str:
    if not names:
        return ""
    lines = [
        "Resolved Cricsheet player names — use these EXACT strings in SQL (batter/bowler columns):"
    ]
    for name in names:
        lines.append(f"- {name}")
    lines.append(
        "If multiple names match, pick the one that fits the question. "
        "Never use display names like 'Kane Williamson' if the resolved name differs."
    )
    return "\n".join(lines)
