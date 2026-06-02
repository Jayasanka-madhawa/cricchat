"""Run validated SQL against PostgreSQL."""

from sqlalchemy import create_engine, text

from backend.config import DATABASE_URL
from backend.sql_safety import validate_sql


def run_query(sql: str, limit_rows: int = 100) -> list[dict]:
    """Execute read-only SQL and return rows as list of dicts."""
    safe_sql = validate_sql(sql)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text(safe_sql))
        if not result.returns_rows:
            return []
        columns = list(result.keys())
        rows = []
        for i, row in enumerate(result):
            if i >= limit_rows:
                break
            rows.append(dict(zip(columns, row)))
    return rows
