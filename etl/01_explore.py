"""
Step 1 — Explore ONE match file.

Goal: see the fields we'll store in the deliveries table.

Run:
    python etl/01_explore.py
"""

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "all_json.zip"


def main() -> None:
    print("=" * 60)
    print("STEP 1 — Explore one Cricsheet match")
    print("=" * 60)

    with zipfile.ZipFile(ZIP_PATH) as zf:
        json_files = [n for n in zf.namelist() if n.endswith(".json")]
        sample_file = json_files[0]
        match = json.loads(zf.read(sample_file))

    info = match["info"]
    inn = match["innings"][0]
    ball = inn["overs"][0]["deliveries"][0]

    print(f"\n📁 File: {sample_file}")
    print(f"   Teams : {info['teams']}")
    print(f"   Format: {info['match_type']}")
    print(f"   Venue : {info.get('venue', 'N/A')}")

    print(f"\n📊 Innings 1: {inn['team']}")
    print(f"   Powerplays: {inn.get('powerplays', 'none')}")

    print("\n🏏 One delivery (→ one row in deliveries table):")
    print(f"   batter       : {ball.get('batter')}")
    print(f"   non_striker  : {ball.get('non_striker')}  ← partnership stats")
    print(f"   bowler       : {ball.get('bowler')}       ← bowling stats")
    print(f"   runs (bat)   : {ball['runs']['batter']}")
    print(f"   runs (total) : {ball['runs']['total']}")

    print("\n✅ Key takeaway:")
    print("   ONE deliveries table stores ALL of this.")
    print("   SQL computes batting, bowling, partnerships, powerplay — anything.")
    print("\nNext: python etl/02_parse_deliveries.py")


if __name__ == "__main__":
    main()
