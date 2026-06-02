# Phase 2 — Chroma knowledge base (RAG)

**Goal:** Give the chatbot context so it can write correct SQL.

Chroma stores **documents** (schema, examples, player names) — NOT ball-by-ball data.
Ball data stays in PostgreSQL from Phase 1.

---

## What you'll learn

| Step | Script | Concept |
|------|--------|---------|
| 1 | Read `knowledge/*.md` | What context the LLM needs |
| 2 | `01_build_chroma.py` | Embed docs → Chroma vector DB |
| 3 | `02_test_retrieval.py` | Ask a question → see relevant chunks |

---

## Setup

```bash
cd /Users/jayasanka/Documents/cricchat
source .venv/bin/activate
pip install -r rag/requirements.txt
```

---

## Step 1 — Read the knowledge files

Open and skim these (you can edit them later):

```
rag/knowledge/
├── schema.md           ← table columns
├── stat_definitions.md ← SR, economy, average formulas
├── player_aliases.md   ← kohli → V Kohli
└── sql_examples.md     ← question → SQL pairs
```

**Key idea:** When user asks *"Kohli strike rate in ODI"*, Chroma retrieves
the strike rate formula + an example SQL query. The LLM (Phase 3) uses that
to generate new SQL.

---

## Step 2 — Build Chroma

```bash
python rag/01_build_chroma.py
```

Creates: `chroma_db/` (local vector database)

Expected output:
```
Indexed 20+ documents into Chroma
Collection: cricchat_knowledge
```

---

## Step 3 — Test retrieval

```bash
python rag/02_test_retrieval.py "Kohli strike rate in ODI"
python rag/02_test_retrieval.py "Sangakkara when Mahela at other end"
python rag/02_test_retrieval.py "Bumrah economy first 6 overs T20"
```

You should see 3 relevant chunks per question (schema, example SQL, aliases).

---

## Phase 2 done when

- [ ] `chroma_db/` folder exists
- [ ] Retrieval returns SQL examples for Kohli / Bumrah / Sangakkara questions
- [ ] You understand: RAG = retrieve context, SQL = get numbers from Postgres

---

## Next: Phase 3

FastAPI `/chat` endpoint — RAG + OpenAI → generate SQL → run on Postgres → answer.
