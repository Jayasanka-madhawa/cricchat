# CricChat — build plan (generalized)

**Goal:** A cricket chatbot that answers **any stat question** answerable from ball-by-ball data.

**Examples it should handle (same table, different SQL):**
- *Kohli average balls to 50 in ODIs*
- *Bumrah bowling average in powerplay T20*
- *Sangakkara strike rate when Mahela is at the other end*
- *Most runs in death overs in IPL 2023*
- *Head-to-head: Kohli vs Anderson*

No pre-built milestone columns. No new ETL per question type.

---

## Core idea

```
Store FACTS (every ball)  →  Compute ANY stat with SQL at question time
```

---

## Architecture

```
all_json.zip
     │  ETL (Pandas)
     ▼
PostgreSQL
  ├── matches      (~22k rows)   context
  ├── players      (~15k rows)   names
  └── deliveries   (~11M rows)   ★ one row per ball
     │
     ▼
Chroma (RAG)     schema docs, SQL examples, player aliases
     │
     ▼
FastAPI /chat    LLM generates SQL → runs on Postgres → natural answer
     │
     ▼
Next.js          chat UI
```

---

## Tech stack

| Layer | Tool |
|-------|------|
| Frontend | Next.js |
| Backend | FastAPI |
| Database | PostgreSQL |
| ETL | Python + Pandas |
| AI | OpenAI (Text-to-SQL) |
| Vector DB | Chroma (schema + examples, not ball data) |

---

## PostgreSQL schema

### `deliveries` — the heart of everything

| Column | Example | Used for |
|--------|---------|----------|
| `match_id` | 1000851 | join to matches |
| `innings_num` | 1 | innings filter |
| `over_num` | 5 | powerplay, death overs |
| `batting_team` | Sri Lanka | team filter |
| `bowling_team` | India | bowling context |
| `batter` | KC Sangakkara | batting stats |
| `non_striker` | DPMD Jayawardene | **partnership stats** |
| `bowler` | JJ Bumrah | bowling stats |
| `runs_batter` | 4 | runs off bat |
| `runs_extras` | 0 | extras on ball |
| `runs_total` | 4 | economy, conceded |
| `is_wide` | false | legal ball count |
| `is_wicket` | true | bowling wickets |
| `dismissal_kind` | bowled | dismissal type |
| `player_out` | SC Cook | who got out |
| `match_type` | T20 | ODI / Test / T20 |
| `match_date` | 2016-11-11 | year filters |
| `is_powerplay` | true | powerplay stats |

### `matches` — match context
`match_id`, `match_date`, `match_type`, `team1`, `team2`, `venue`, `gender`

### `players` — name lookup
`player_name`, `player_id` (Cricsheet registry)

---

## Example SQL (all from `deliveries`)

**Kohli ODI strike rate**
```sql
SELECT ROUND(100.0 * SUM(runs_batter) / NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1)
FROM deliveries
WHERE batter = 'V Kohli' AND match_type = 'ODI';
```

**Bumrah powerplay T20 bowling average**
```sql
SELECT ROUND(SUM(runs_total)::numeric / NULLIF(COUNT(*) FILTER (WHERE is_wicket), 0), 1)
FROM deliveries
WHERE bowler = 'JJ Bumrah' AND match_type = 'T20' AND is_powerplay;
```

**Sangakkara SR when Mahela at other end**
```sql
SELECT ROUND(100.0 * SUM(runs_batter) / NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1)
FROM deliveries
WHERE batter = 'KC Sangakkara' AND non_striker = 'DPMD Jayawardene';
```

**Death overs (T20: overs 16–19, 0-indexed)**
```sql
SELECT batter, SUM(runs_batter) AS runs
FROM deliveries
WHERE match_type = 'T20' AND over_num >= 15
GROUP BY batter ORDER BY runs DESC LIMIT 10;
```

---

## Build phases

### Phase 1 — General ETL (you are here)
| Step | Script | Output |
|------|--------|--------|
| 1 | `01_explore.py` | Understand JSON |
| 2 | `02_parse_deliveries.py` | `data/*.parquet` |
| 3 | `03_load_db.py` | PostgreSQL |
| 4 | `04_verify.sql` | Prove diverse questions work |

### Phase 2 — RAG knowledge base (Chroma)
- Embed full schema + 20+ diverse SQL examples
- Player alias map (kohli → V Kohli, bumrah → JJ Bumrah)
- Stat definitions (SR, economy, powerplay = overs 1–6)

### Phase 3 — Text-to-SQL API (FastAPI)
- `POST /chat` with read-only SQL safety
- RAG retrieve → LLM → SQL → execute → answer

### Phase 4 — Next.js chat UI

---

## What we removed (old narrow design)

| Removed | Why |
|---------|-----|
| `player_innings` table | Pre-computed batting only |
| `balls_to_50` column | Can compute from deliveries |
| Question-specific ETL | SQL handles any question |

---

## Project structure

```
cricchat/
├── all_json.zip
├── docker-compose.yml
├── BUILD.md
├── etl/
│   ├── README.md
│   ├── 01_explore.py
│   ├── 02_parse_deliveries.py   ← generalized parser
│   └── 03_load_db.py
├── sql/
│   ├── schema.sql               ← table docs
│   └── 04_verify.sql            ← diverse test queries
├── backend/                     (Phase 3)
└── frontend/                    (Phase 4)
```

---

## Next action

Follow `etl/README.md` step by step. Start with Step 1.

If you already ran the old `02_parse_all.py`, delete old data first:

```bash
rm -rf data/
```

Then run `02_parse_deliveries.py`.
