# Phase 1 — General ETL (step by step)

**Goal:** Load every ball from Cricsheet into PostgreSQL.

**Do one step at a time.** Confirm it works before moving on.

---

## What you're building

```
all_json.zip  →  deliveries.parquet (~11M rows)  →  PostgreSQL
                  matches.parquet
                  players.parquet
```

One row in `deliveries` = one ball. All stats computed with SQL later.

---

## Setup (once)

```bash
cd /Users/jayasanka/Documents/cricchat
python3 -m venv .venv
source .venv/bin/activate
pip install -r etl/requirements.txt
```

If you have **old** narrow data from before:

```bash
rm -rf data/
```

---

## Step 1 — Explore one match (~15 min)

```bash
python etl/01_explore.py
```

**Learn:** `batter`, `bowler`, `non_striker`, `powerplays`

**Check you see:**
- `non_striker` on every ball → enables partnership questions
- `powerplays` on innings → enables powerplay filters

---

## Step 2 — Parse all matches (~5–10 min)

```bash
python etl/02_parse_deliveries.py
```

Creates:
```
data/matches.parquet       ~22k rows
data/players.parquet       ~15k rows
data/deliveries.parquet    ~11M rows  ← the big one
```

Inspect:

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/deliveries.parquet')
print(df.columns.tolist())
print(df.head(2))
print(len(df), 'balls')
"
```

---

## Step 3 — Start PostgreSQL

Docker Desktop must be running.

```bash
docker compose up -d
docker compose ps
```

---

## Step 4 — Load into PostgreSQL (~5–15 min)

```bash
python etl/03_load_db.py
```

Loading 11M rows takes a few minutes. Indexes are created after load.

---

## Step 5 — Verify diverse questions

```bash
docker compose exec postgres psql -U cricchat -d cricchat -f /sql/04_verify.sql
```

You should see answers for:
1. Kohli ODI strike rate
2. Bumrah powerplay T20 economy
3. Sangakkara SR with Mahela at other end
4. Match/ball counts

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Out of memory on Step 2 | Close other apps; script builds in memory |
| Load very slow | Normal for 11M rows |
| Old `player_innings` errors | Delete `data/`, use new scripts |

---

## Phase 1 done when

- [ ] `deliveries` has ~11 million rows
- [ ] Sangakkara + Mahela query returns ~68 SR
- [ ] Bumrah powerplay query returns a number
- [ ] You understand: **one table, many questions**

Then: **Phase 2** — Chroma knowledge base for the chatbot.
