# CricChat

Ask cricket stats in plain English — powered by Cricsheet ball-by-ball data, PostgreSQL, RAG, and OpenAI Text-to-SQL.

**Examples:** *Kohli strike rate in ODI* · *Bumrah economy in T20 powerplay* · *Sangakkara when Mahela is non-striker*

---
 
## Quick links

| Doc | For |
|-----|-----|
| **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** | **Start here** — full learning path, architecture, deploy, troubleshooting |
| [BUILD.md](BUILD.md) | Design plan and schema overview |
| [etl/README.md](etl/README.md) | Phase 1 — load data |
| [rag/README.md](rag/README.md) | Phase 2 — Chroma knowledge base |
| [backend/README.md](backend/README.md) | Phase 3 — FastAPI API |
| [frontend/README.md](frontend/README.md) | Phase 4 — Next.js UI |
| [deploy/EASY_DEPLOY.md](deploy/EASY_DEPLOY.md) | Production — Render + Vercel + AWS RDS |

---

## Live demo

- **App:** https://cricchat.vercel.app  
- **API:** https://cricchat.onrender.com  

---

## Local run (minimal)

```bash
# 1. Data + DB (first time only — long)
docker compose up -d
source .venv/bin/activate
pip install -r etl/requirements.txt -r backend/requirements.txt -r rag/requirements.txt
python etl/02_parse_deliveries.py && python etl/03_load_db.py
python rag/01_build_chroma.py

# 2. Secrets
cp backend/.env.example .env   # add OPENAI_API_KEY

# 3. API + UI
uvicorn backend.main:app --reload
cd frontend && npm install && npm run dev
```

See **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** for full details.

---

## Stack

PostgreSQL · FastAPI · Chroma · OpenAI · Next.js · Docker
