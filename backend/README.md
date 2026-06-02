# Phase 3 — Chat API (RAG + Text-to-SQL)

Connects Phase 1 (PostgreSQL) + Phase 2 (Chroma) + OpenAI.

---

## How it works

```
POST /chat { "question": "..." }
        ↓
① Chroma — retrieve schema + SQL examples
        ↓
② OpenAI — generate SELECT query
        ↓
③ PostgreSQL — run query (read-only)
        ↓
④ OpenAI — format natural language answer
        ↓
{ "answer": "...", "sql": "...", "row_count": 1 }
```

---

## Setup

### 1. Prerequisites

- Phase 1 done: `docker compose up -d`, data loaded
- Phase 2 done: `python rag/01_build_chroma.py`
- OpenAI API key: https://platform.openai.com/api-keys

### 2. Install dependencies

```bash
cd /Users/jayasanka/Documents/cricchat
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Configure API key

```bash
cp backend/.env.example .env
# Edit .env — add your OPENAI_API_KEY
```

---

## Step 1 — Test with CLI (easiest)

No server needed:

```bash
python backend/chat_cli.py "Kohli strike rate in ODI"
```

Interactive mode:

```bash
python backend/chat_cli.py
```

You should see:
- Natural language answer
- SQL the LLM generated
- Row count

Try:
- `Sangakkara strike rate when Mahela at other end`
- `Bumrah economy in first 6 overs T20`
- `Maxwell T20 strike rate`

---

## Step 2 — Start FastAPI server

```bash
uvicorn backend.main:app --reload
```

Open: http://localhost:8000/docs (Swagger UI)

Or curl:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Kohli strike rate in ODI"}'
```

---

## Project files

```
backend/
├── main.py          ← FastAPI app (/chat, /health)
├── agent.py         ← RAG + LLM pipeline
├── retriever.py     ← Chroma lookup
├── db.py            ← run SQL on Postgres
├── sql_safety.py    ← block non-SELECT queries
├── chat_cli.py      ← terminal chat
└── config.py
```

---

## Safety

- Only `SELECT` queries allowed
- Blocks INSERT, UPDATE, DELETE, DROP, etc.
- Results capped at 100 rows

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `OPENAI_API_KEY not set` | Create `.env` with your key |
| `Connection refused` Postgres | `docker compose up -d` |
| `Chroma not built` | `python rag/01_build_chroma.py` |
| Bad SQL / wrong player name | Add examples to `rag/knowledge/` and rebuild Chroma |

---

## Phase 3 done when

- [ ] CLI answers Kohli strike rate correctly (~93.8)
- [ ] Sangakkara + Mahela partnership question works
- [ ] `/chat` API returns JSON with answer + sql

---

## Next: Phase 4

Next.js frontend calling `POST /chat`.
