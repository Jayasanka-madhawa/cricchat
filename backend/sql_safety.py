"""Validate that generated SQL is read-only."""

import re

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str) -> str:
    """
    Ensure SQL is a single SELECT statement.
    Returns cleaned SQL or raises ValueError.
    """
    sql = sql.strip().rstrip(";")

    # Strip markdown code fences if LLM wrapped SQL
    if "```" in sql:
        match = re.search(r"```(?:sql)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()

    upper = sql.upper().lstrip()
    # Allow CTEs: WITH innings AS (...) SELECT ...
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise ValueError("Only SELECT queries are allowed.")
    if upper.startswith("WITH") and "SELECT" not in upper:
        raise ValueError("Only SELECT queries are allowed.")

    if FORBIDDEN.search(sql):
        raise ValueError("Query contains forbidden keywords.")

    return sql
