"""
Step 2 — Parse ALL matches into a general deliveries table.

Goal: one row per ball. Store RAW facts only.
      No pre-computed stats, no guessed powerplay flags.
      The chatbot computes phases (powerplay, death overs) via SQL at query time.

Run:
    python etl/02_parse_deliveries.py

Output:
    data/matches.parquet
    data/players.parquet
    data/deliveries.parquet        (~11 million rows)
    data/innings_powerplays.parquet (only where Cricsheet provides it — may be empty rows for Tests)
"""

import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "all_json.zip"
DATA_DIR = ROOT / "data"


def other_team(teams: list, batting_team: str) -> str:
    if len(teams) < 2:
        return ""
    return teams[1] if teams[0] == batting_team else teams[0]


def main() -> None:
    print("=" * 60)
    print("STEP 2 — Parse all matches → deliveries (raw facts)")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)

    match_rows = []
    player_rows = {}
    delivery_rows = []
    powerplay_rows = []

    with zipfile.ZipFile(ZIP_PATH) as zf:
        json_files = [n for n in zf.namelist() if n.endswith(".json")]
        total = len(json_files)
        print(f"\nParsing {total:,} matches…")

        for i, fname in enumerate(json_files, 1):
            match_id = Path(fname).stem
            m = json.loads(zf.read(fname))
            info = m["info"]
            teams = info.get("teams", ["", ""])
            match_type = info.get("match_type")
            match_date = (info.get("dates") or [None])[0]

            match_rows.append({
                "match_id": match_id,
                "match_date": match_date,
                "match_type": match_type,
                "gender": info.get("gender"),
                "team1": teams[0] if teams else None,
                "team2": teams[1] if len(teams) > 1 else None,
                "venue": info.get("venue"),
            })

            for pname, pid in info.get("registry", {}).get("people", {}).items():
                player_rows[pname] = pid

            for inn_num, inn in enumerate(m.get("innings", []), 1):
                batting_team = inn.get("team", "")
                bowling_team = other_team(teams, batting_team)

                # Store Cricsheet powerplay blocks as-is (no interpretation)
                for pp in inn.get("powerplays") or []:
                    powerplay_rows.append({
                        "match_id": match_id,
                        "innings_num": inn_num,
                        "pp_from": pp.get("from"),
                        "pp_to": pp.get("to"),
                        "pp_type": pp.get("type"),
                    })

                for over_block in inn.get("overs", []):
                    over_num = over_block.get("over", 0)

                    for d in over_block.get("deliveries", []):
                        extras = d.get("extras") or {}
                        wickets = d.get("wickets") or []
                        runs = d.get("runs") or {}
                        w = wickets[0] if wickets else {}

                        delivery_rows.append({
                            "match_id": match_id,
                            "innings_num": inn_num,
                            "over_num": over_num,
                            "batting_team": batting_team,
                            "bowling_team": bowling_team,
                            "batter": d.get("batter"),
                            "non_striker": d.get("non_striker"),
                            "bowler": d.get("bowler"),
                            "runs_batter": runs.get("batter", 0),
                            "runs_extras": runs.get("extras", 0),
                            "runs_total": runs.get("total", 0),
                            "is_wide": bool(extras.get("wides")),
                            "is_wicket": bool(wickets),
                            "dismissal_kind": w.get("kind"),
                            "player_out": w.get("player_out"),
                            "match_type": match_type,
                            "match_date": match_date,
                        })

            if i % 3000 == 0:
                print(f"   … {i:,} / {total:,}")

    print("\nBuilding DataFrames…")
    df_matches = pd.DataFrame(match_rows)
    df_players = pd.DataFrame(
        [{"player_name": n, "player_id": pid} for n, pid in player_rows.items()]
    )
    df_deliveries = pd.DataFrame(delivery_rows)
    df_powerplays = pd.DataFrame(powerplay_rows)

    print("Saving Parquet…")
    df_matches.to_parquet(DATA_DIR / "matches.parquet", index=False)
    df_players.to_parquet(DATA_DIR / "players.parquet", index=False)
    df_deliveries.to_parquet(DATA_DIR / "deliveries.parquet", index=False)
    df_powerplays.to_parquet(DATA_DIR / "innings_powerplays.parquet", index=False)

    print(f"\n✅ Saved to {DATA_DIR}/")
    print(f"   matches            : {len(df_matches):,} rows")
    print(f"   players            : {len(df_players):,} rows")
    print(f"   deliveries         : {len(df_deliveries):,} rows")
    print(f"   innings_powerplays : {len(df_powerplays):,} rows (raw from Cricsheet)")

    print("\n📋 Sample delivery:")
    print(df_deliveries.head(1).T.to_string())

    print("\n💡 Powerplay is NOT stored on each ball.")
    print("   Chatbot/SQL uses over_num + match_type, or joins innings_powerplays when needed.")

    print("\nNext: docker compose up -d")
    print("Then: python etl/03_load_db.py")


if __name__ == "__main__":
    main()
