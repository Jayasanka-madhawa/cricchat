# CricChat — Developer & Learning Guide

A complete guide for understanding, running, and deploying **CricChat**: a generalized cricket stats chatbot built from Cricsheet ball-by-ball data.

**Read this first** if you are new to the project or starting again from scratch.

---

## Table of contents

1. [What you are building](#1-what-you-are-building)
2. [Core design decisions](#2-core-design-decisions)
3. [Architecture](#3-architecture)
4. [Project structure](#4-project-structure)
5. [Prerequisites](#5-prerequisites)
6. [Phase 1 — ETL and PostgreSQL](#6-phase-1--etl-and-postgresql)
7. [Phase 2 — RAG (Chroma)](#7-phase-2--rag-chroma)
8. [Phase 3 — API (FastAPI + OpenAI)](#8-phase-3--api-fastapi--openai)
9. [Phase 4 — Frontend (Next.js)](#9-phase-4--frontend-nextjs)
10. [Production deploy (Render + Vercel + RDS)](#10-production-deploy-render--vercel--rds)
11. [Environment variables](#11-environment-variables)
12. [Verification queries](#12-verification-queries)
13. [Troubleshooting](#13-troubleshooting)
14. [Costs and when to shut down](#14-costs-and-when-to-shut-down)
15. [What we learned (mistakes and fixes)](#15-what-we-learned-mistakes-and-fixes)
16. [Further reading](#16-further-reading)

---

## 1. What you are building

**CricChat** answers natural-language cricket questions using real match data:

- *Kohli strike rate in ODI*
- *Bumrah economy in first 6 overs T20*
- *Sangakkara strike rate when Mahela is non-striker*

You do **not** hardcode one function per question type. Instead:

```
Store every ball as a row  →  LLM writes SQL  →  PostgreSQL computes the stat
```

Data source: [Cricsheet](https://cricsheet.org/) (`all_json.zip`, ~22,000 matches, ~11M deliveries).

---

## 2. Core design decisions

| Decision | Why |
|----------|-----|
| **One `deliveries` table** | Any stat = SQL at query time; no new ETL per question |
| **No pre-computed columns** (e.g. `balls_to_50`) | Avoid narrow schema; SQL window functions handle it |
| **No `is_powerplay` flag in ETL** | Powerplay rules differ by format; use `over_num` in SQL |
| **RAG on knowledge docs only** | Chroma holds schema + examples, not 11M balls |
| **Text-to-SQL, not document RAG on balls** | Facts live in Postgres; LLM only needs how to query |
| **Read-only SQL** | Block INSERT/UPDATE/DELETE in `backend/sql_safety.py` |
| **Exact Cricsheet player names** | e.g. `V Kohli`, not `Virat Kohli` |
| **No LangChain** | Small linear pipeline; easier to learn and debug |

### Powerplay in SQL (not ETL)

| Format | User says | SQL filter |
|--------|-----------|------------|
| T20 first 6 overs | powerplay / first 6 | `over_num <= 5` |
| ODI first 10 overs | first 10 / PP1 | `over_num <= 9` |
| T20 death (17–20) | death overs | `over_num >= 15` |
| Career stat | "Kohli SR in ODI" | **no** `over_num` filter |

`over_num` is **0-indexed** (0 = 1st over).

---

## 3. Architecture

### Local development

```
all_json.zip
     │  etl/ (Pandas)
     ▼
PostgreSQL (Docker)  ←  deliveries, matches, players
     │
     ├── Chroma (rag/)     schema, SQL examples, aliases
     │
     ├── FastAPI (backend/)  POST /chat
     │
     └── Next.js (frontend/)  browser UI
              │
              └── OpenAI API (SQL + answer)
```

### Production (easy path)

```
https://cricchat.vercel.app     (Vercel — Next.js)
        │
        ▼
https://cricchat.onrender.com   (Render — Docker / FastAPI)
        │
        ├── Chroma (built inside Docker image at deploy)
        ├── AWS RDS PostgreSQL (eu-north-1)
        └── OpenAI API
```

### Request flow (`POST /chat`)

1. User question
2. **Chroma** — retrieve top-k chunks from `rag/knowledge/*.md`
3. **OpenAI** — generate one `SELECT` query
4. **`sql_safety.py`** — validate read-only
5. **PostgreSQL** — execute query
6. **OpenAI** — format natural language answer
7. Return `{ answer, sql, row_count }`

**Note:** Each request is **stateless** (no chat memory). Ask full questions, not "what format?" as a follow-up.

---

## 4. Project structure

```
cricchat/
├── all_json.zip              # Cricsheet data (you provide; gitignored)
├── BUILD.md                  # Original build plan
├── DEVELOPER_GUIDE.md        # This file
├── Dockerfile                # API image for Render
├── docker-compose.yml        # Local Postgres
├── .env                      # Local secrets (gitignored)
│
├── etl/
│   ├── README.md
│   ├── 01_explore.py
│   ├── 02_parse_deliveries.py
│   └── 03_load_db.py
│
├── sql/
│   ├── schema.sql
│   └── 04_verify.sql
│
├── rag/
│   ├── README.md
│   ├── 01_build_chroma.py
│   ├── 02_test_retrieval.py
│   └── knowledge/
│       ├── schema.md
│       ├── stat_definitions.md
│       ├── player_aliases.md
│       └── sql_examples.md
│
├── backend/
│   ├── README.md
│   ├── main.py               # FastAPI
│   ├── agent.py              # RAG → SQL → answer
│   ├── retriever.py
│   ├── db.py
│   ├── sql_safety.py
│   ├── chat_cli.py
│   └── config.py
│
├── frontend/
│   ├── README.md
│   └── app/page.tsx          # Chat UI
│
├── deploy/
│   └── EASY_DEPLOY.md        # Render + Vercel steps
│
├── data/                     # Parquet (gitignored)
├── chroma_db/                # Vector DB (gitignored)
└── .venv/                    # Python env (gitignored)
```

---

## 5. Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.9+ | ETL, backend, RAG |
| Node.js 20+ | Frontend |
| Docker Desktop | Local PostgreSQL |
| `all_json.zip` | From Cricsheet |
| OpenAI API key | Text-to-SQL + answers ([billing required](https://platform.openai.com)) |
| Git + GitHub | Deploy |

Optional for cloud DB upload: `libpq` (`brew install libpq`) for `pg_dump` / `pg_restore`.

---

## 6. Phase 1 — ETL and PostgreSQL

**Goal:** Load ~11M delivery rows into PostgreSQL.

**Detailed steps:** `etl/README.md`

### Quick start (after setup)

```bash
cd cricchat
python3 -m venv .venv
source .venv/bin/activate
pip install -r etl/requirements.txt

docker compose up -d
python etl/02_parse_deliveries.py    # → data/*.parquet (long)
python etl/03_load_db.py

docker compose exec postgres psql -U cricchat -d cricchat -f /sql/04_verify.sql
```

### Tables

| Table | Rows (approx) | Role |
|-------|----------------|------|
| `matches` | ~22k | match_type, date, teams |
| `players` | ~15k | Cricsheet player names |
| `deliveries` | ~11M | **one row per ball** |
| `innings_powerplays` | varies | raw Cricsheet PP blocks (optional) |

### Local DB connection

```
postgresql://cricchat:cricchat@localhost:5432/cricchat
```

---

## 7. Phase 2 — RAG (Chroma)

**Goal:** Embed knowledge docs so the LLM can write better SQL.

**Detailed steps:** `rag/README.md`

Chroma does **not** store ball data — only markdown in `rag/knowledge/`.

```bash
pip install -r rag/requirements.txt
python rag/01_build_chroma.py
python rag/02_test_retrieval.py "Kohli strike rate in ODI"
```

Output: `chroma_db/` (gitignored).

**Improving answers:** Add examples to `sql_examples.md`, clarify rules in `stat_definitions.md`, add aliases in `player_aliases.md`, then rebuild Chroma.

---

## 8. Phase 3 — API (FastAPI + OpenAI)

**Goal:** `POST /chat` — question in, answer + SQL out.

**Detailed steps:** `backend/README.md`

### Setup

```bash
pip install -r backend/requirements.txt
cp backend/.env.example .env
# Edit .env — OPENAI_API_KEY, DATABASE_URL
```

### Run locally

```bash
# Terminal 1 — Postgres
docker compose up -d

# Terminal 2 — API
source .venv/bin/activate
uvicorn backend.main:app --reload
```

### CLI (no server)

```bash
python backend/chat_cli.py "Kohli strike rate in ODI"
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{ "status": "ok" }` |
| POST | `/chat` | Body: `{ "question": "..." }` |

---

## 9. Phase 4 — Frontend (Next.js)

**Goal:** Browser chat UI.

**Detailed steps:** `frontend/README.md`

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

Set in `frontend/.env.local` (optional locally):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Important:** `NEXT_PUBLIC_*` is baked in at **build time** on Vercel — set env var in Vercel dashboard and **redeploy** after changes.

---

## 10. Production deploy (Render + Vercel + RDS)

**Full steps:** `deploy/EASY_DEPLOY.md`

### Summary

| Component | Service | URL (example) |
|-----------|---------|----------------|
| Frontend | Vercel (`frontend/`) | https://cricchat.vercel.app |
| API | Render (Dockerfile) | https://cricchat.onrender.com |
| Database | AWS RDS PostgreSQL | `database-1.*.eu-north-1.rds.amazonaws.com` |

### Deploy flow (CD)

- Push to `main` on GitHub → **Render** rebuilds API, **Vercel** rebuilds UI (GitHub CD).
- **Manual Deploy** on Render after env var changes (e.g. CORS).

### RDS setup (one-time)

1. RDS PostgreSQL 16, `db.t3.micro`, 20 GB, database name `cricchat`
2. **Publicly accessible: Yes**
3. Security group: PostgreSQL **5432** from **My IP** + **`0.0.0.0/0`** (for Render)
4. Upload data:

```bash
docker compose exec -T postgres pg_dump -U cricchat -d cricchat -Fc > cricchat.dump

export RDS_URL="postgresql://postgres:PASSWORD@ENDPOINT:5432/cricchat?sslmode=require"
docker run --rm postgres:16 psql "$RDS_URL" -c "CREATE DATABASE cricchat;"  # if needed
docker run --rm -v "$(pwd)/cricchat.dump:/backup.dump:ro" postgres:16 \
  pg_restore -d "$RDS_URL" --no-owner --no-acl /backup.dump
```

### CORS (required for browser)

`backend/config.py` reads **`CORS_ORIGINS`** (comma-separated).

On Render set:

```
CORS_ORIGINS=https://cricchat.vercel.app,http://localhost:3000
```

Push code + Manual Deploy after changes.

### AWS notes

- **App Runner** not available in `eu-north-1` and closed to new customers (2026) — we used Render instead.
- Use **personal AWS account** for RDS; keep **company CLI profile** separate (`AWS_PROFILE=cricchat-personal`).
- **IAM user** `cricchat-cli` needs permissions (e.g. AdministratorAccess for learning) for ECR/RDS setup.

---

## 11. Environment variables

### Local `.env` (project root)

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=postgresql://cricchat:cricchat@localhost:5432/cricchat
```

### Render (API)

| Variable | Example / notes |
|----------|-----------------|
| `DATABASE_URL` | RDS URL with `?sslmode=require` |
| `OPENAI_API_KEY` | Required |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `CORS_ORIGINS` | `https://cricchat.vercel.app,http://localhost:3000` |
| `XDG_CACHE_HOME` | `/app/.cache` |

### Vercel (frontend)

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `https://cricchat.onrender.com` (no trailing slash) |

**Never commit** `.env`, API keys, or RDS passwords to Git.

---

## 12. Verification queries

Run after Phase 1 or after RDS restore:

```sql
-- Row count
SELECT COUNT(*) FROM deliveries;

-- Kohli ODI strike rate (~93.8)
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1)
FROM deliveries
WHERE batter = 'V Kohli' AND match_type = 'ODI';

-- Bumrah T20 powerplay economy (~6.79)
SELECT ROUND(SUM(runs_total)::numeric /
       (COUNT(*) FILTER (WHERE NOT is_wide) / 6.0), 2)
FROM deliveries
WHERE bowler = 'JJ Bumrah' AND match_type = 'T20' AND over_num <= 5;

-- Sangakkara + Mahela (~68.0)
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1)
FROM deliveries
WHERE batter = 'KC Sangakkara' AND non_striker = 'DPMD Jayawardene';
```

Full file: `sql/04_verify.sql`

---

## 13. Troubleshooting

### ETL / Postgres

| Problem | Fix |
|---------|-----|
| Connection refused | `docker compose up -d` |
| Tables missing | Run `03_load_db.py` after parse |

### OpenAI

| Problem | Fix |
|---------|-----|
| `insufficient_quota` | Add billing on OpenAI account |
| Wrong stat / bad SQL | Improve `rag/knowledge/`, rebuild Chroma; tighten `agent.py` prompts |

### LLM adds wrong `over_num`

Career questions must **not** filter powerplay. See `stat_definitions.md` and Example 1 in `sql_examples.md`.

### Chroma PermissionError

Scripts set `XDG_CACHE_HOME` to project `.cache/`.

### Deploy — browser "Could not reach API"

| Cause | Fix |
|-------|-----|
| Missing `NEXT_PUBLIC_API_URL` on Vercel | Set + **redeploy** |
| Still calls `localhost:8000` | Env not set at build time |

### CORS error

| Cause | Fix |
|-------|-----|
| `CORS_ORIGINS` missing Vercel URL | Set on Render: `https://cricchat.vercel.app` |
| Old code ignored env | Use `backend/main.py` with `CORS_ORIGINS` from config |

### RDS connection from Mac

| Error | Fix |
|-------|-----|
| Private IP / connection refused | **Publicly accessible: Yes** |
| Timeout | Security group **5432** from **My IP** |
| `pg_dump` not found | `brew install libpq` or use Docker `postgres:16` |

### Render slow first request

Free tier **spins down** — wait 30–60s on first question after idle.

### Follow-up questions fail

No chat history — ask one full sentence: *"Which formats has Ishan Kishan played in?"* not *"what format?"*

### Player names

Search: `SELECT player_name FROM players WHERE player_name ILIKE '%kohli%';`  
Use exact Cricsheet name in SQL.

---

## 14. Costs and when to shut down

| Service | Typical cost |
|---------|----------------|
| Render Free | $0 (sleeps when idle) |
| Vercel Hobby | $0 |
| AWS RDS | $0 free tier ~12 months, then ~$15–20/mo if running |
| OpenAI | Pay per API usage |
| ECR (if used) | Negligible storage |

**Card on Render** = verification; not auto-charged on Free plan.

### When project ends — delete to stop charges

1. Render → Delete Web Service  
2. Vercel → Delete Project  
3. RDS → Delete instance (loses cloud DB) or **Stop** temporarily  
4. Keep local: `docker compose` + code on GitHub  

Set AWS **billing budget alert** (e.g. $10/month).

---

## 15. What we learned (mistakes and fixes)

| Issue | Lesson |
|-------|--------|
| Pre-computed `is_powerplay` | Wrong for multi-format; use `over_num` in SQL |
| Kohli SR with `over_num <= 9` | LLM over-applied powerplay; fixed prompts + knowledge |
| No chat memory | Each `/chat` call is independent |
| `CORS_ORIGINS` on Render ignored | Was hardcoded localhost; fixed in `config.py` + `main.py` |
| Vercel without `NEXT_PUBLIC_API_URL` | Defaults to localhost; must redeploy after env |
| AWS App Runner in Stockholm | Not supported; used Render |
| Company vs personal AWS CLI | Use separate profile; RDS in personal account |
| `pg_dump` not on Mac | Use Docker: `docker compose exec -T postgres pg_dump ...` |
| RDS private IP | Need **Publicly accessible** + security group rules |
| Exposed passwords in chat | Rotate RDS password and IAM keys |
| Ishan Kishan "no data" | Vague follow-up; exact names in `players` table work |

---

## 16. Further reading

| Doc | Topic |
|-----|--------|
| `BUILD.md` | Original architecture plan |
| `etl/README.md` | Phase 1 step-by-step |
| `rag/README.md` | Phase 2 Chroma |
| `backend/README.md` | Phase 3 API |
| `frontend/README.md` | Phase 4 UI |
| `deploy/EASY_DEPLOY.md` | Production deploy |
| `sql/schema.sql` | Column reference |
| `sql/04_verify.sql` | Test queries |

### Suggested learning order (new developer)

1. Read sections 1–3 of this guide  
2. Run Phase 1 locally → verify SQL  
3. Run Phase 2 → test retrieval  
4. Run Phase 3 CLI → one question  
5. Run Phase 4 locally  
6. Deploy with `deploy/EASY_DEPLOY.md`  
7. Add one new question type via `sql_examples.md` + rebuild Chroma  

---

## Live URLs (this deployment)

| Service | URL |
|---------|-----|
| Frontend | https://cricchat.vercel.app |
| API | https://cricchat.onrender.com |
| Health check | https://cricchat.onrender.com/health |

Replace with your URLs if you fork the project.

---

*CricChat — store facts, query with SQL, teach the LLM with RAG.*
