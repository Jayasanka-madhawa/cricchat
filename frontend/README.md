# Phase 4 — Next.js chat UI

Browser chat that calls the FastAPI backend (`POST /chat`).

---

## How it works

```
Browser (localhost:3000)
        ↓  fetch POST /chat
FastAPI (localhost:8000)
        ↓
Chroma + OpenAI + PostgreSQL
        ↓
JSON { answer, sql, row_count } → shown in UI
```

---

## Prerequisites

- Phase 1: Postgres loaded (`docker compose up -d`)
- Phase 2: Chroma built (`python rag/01_build_chroma.py`)
- Phase 3: `.env` with `OPENAI_API_KEY` at project root

---

## Step 1 — Install frontend deps

```bash
cd /Users/jayasanka/Documents/cricchat/frontend
npm install
```

Optional config:

```bash
cp .env.local.example .env.local
# Default API URL is http://localhost:8000
```

---

## Step 2 — Start the API (terminal 1)

From project root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Check: http://localhost:8000/health → `{"status":"ok"}`

---

## Step 3 — Start the frontend (terminal 2)

```bash
cd frontend
npm run dev
```

Open: **http://localhost:3000**

Ask: *Kohli strike rate in ODI*

You should see:
- Natural language answer
- SQL block (toggle with “Show SQL used”)
- Row count

---

## Project files

```
frontend/
├── app/
│   ├── page.tsx       ← chat UI
│   ├── layout.tsx
│   └── globals.css
├── package.json
├── next.config.ts
└── .env.local.example
```

CORS for the browser is configured in `backend/main.py` (allows `localhost:3000`).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| “Could not reach the API” | Run `uvicorn backend.main:app --reload` |
| CORS error in browser console | Restart uvicorn after pulling latest `main.py` |
| OpenAI quota / 500 errors | Check billing; test with `python backend/chat_cli.py "..."` |
| Wrong stats | Same as CLI — improve `rag/knowledge/` and rebuild Chroma |

---

## Phase 4 done when

- [ ] UI loads at localhost:3000
- [ ] Kohli ODI strike rate works (~93.8)
- [ ] SQL toggle shows/hides the query

---

## Production (later)

- Set `NEXT_PUBLIC_API_URL` to your deployed API
- Deploy frontend (e.g. Vercel) and backend separately
