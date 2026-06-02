"""
Step 3 — Load Parquet into PostgreSQL (generalized schema).

Prerequisites:
    docker compose up -d
    python etl/02_parse_deliveries.py

Run:
    python etl/03_load_db.py
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATABASE_URL = "postgresql://cricchat:cricchat@localhost:5432/cricchat"


def main() -> None:
    print("=" * 60)
    print("STEP 3 — Load Parquet → PostgreSQL")
    print("=" * 60)

    required = ["matches.parquet", "players.parquet", "deliveries.parquet", "innings_powerplays.parquet"]
    for f in required:
        if not (DATA_DIR / f).exists():
            raise FileNotFoundError(
                f"Missing {f}. Run: python etl/02_parse_deliveries.py"
            )

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("\n✅ Connected to PostgreSQL")

    with engine.connect() as conn:
        for table in ["deliveries", "innings_powerplays", "matches", "players"]:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        conn.commit()
    print("   Cleared old tables")

    # Load smaller tables first, deliveries last (largest)
    for name in ["matches", "players", "innings_powerplays", "deliveries"]:
        print(f"   Loading {name}…")
        df = pd.read_parquet(DATA_DIR / f"{name}.parquet")
        # Batch load for large deliveries table
        chunksize = 500_000 if name == "deliveries" else None
        if chunksize and len(df) > chunksize:
            for start in range(0, len(df), chunksize):
                chunk = df.iloc[start : start + chunksize]
                chunk.to_sql(
                    name, engine,
                    if_exists="append" if start else "replace",
                    index=False,
                )
                print(f"      … {min(start + chunksize, len(df)):,} / {len(df):,}")
        else:
            df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"   Loaded {name}: {len(df):,} rows")

    print("   Creating indexes (may take a few minutes)…")
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX idx_del_batter ON deliveries(batter)"))
        conn.execute(text("CREATE INDEX idx_del_bowler ON deliveries(bowler)"))
        conn.execute(text("CREATE INDEX idx_del_non_striker ON deliveries(non_striker)"))
        conn.execute(text("CREATE INDEX idx_del_type ON deliveries(match_type)"))
        conn.execute(text("CREATE INDEX idx_del_over ON deliveries(over_num)"))
        conn.execute(text("CREATE INDEX idx_del_match ON deliveries(match_id)"))
        conn.commit()

    with engine.connect() as conn:
        balls = conn.execute(text("SELECT COUNT(*) FROM deliveries")).scalar()
        sanga_sr = conn.execute(text("""
            SELECT ROUND(100.0 * SUM(runs_batter) /
                   NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1)
            FROM deliveries
            WHERE batter = 'KC Sangakkara'
              AND non_striker = 'DPMD Jayawardene'
        """)).scalar()

    print(f"\n📊 Verification:")
    print(f"   Total balls in DB : {balls:,}")
    print(f"   Sangakkara SR with Mahela at other end: {sanga_sr}")

    print("\n✅ Phase 1 complete!")
    print("Run: docker compose exec postgres psql -U cricchat -d cricchat -f /sql/04_verify.sql")


if __name__ == "__main__":
    main()
