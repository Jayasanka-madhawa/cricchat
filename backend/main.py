"""
Phase 3 — FastAPI chat server.

Run:
    cd /Users/jayasanka/Documents/cricchat
    source .venv/bin/activate
    pip install -r backend/requirements.txt
    cp backend/.env.example .env   # add OPENAI_API_KEY
    uvicorn backend.main:app --reload

Test:
    curl -X POST http://localhost:8000/chat \\
      -H "Content-Type: application/json" \\
      -d '{"question": "Kohli strike rate in ODI"}'
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.agent import ask

app = FastAPI(title="CricChat", version="0.1.0")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    sql: str
    row_count: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = ask(question)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sql=result["sql"],
        row_count=len(result["rows"]),
    )
