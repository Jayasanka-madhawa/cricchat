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

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from backend.agent import ask, ask_with_messages
from backend.config import CORS_ORIGINS

app = FastAPI(title="CricChat", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_question_or_messages(self):
        has_question = bool(self.question and self.question.strip())
        has_messages = bool(self.messages)
        if not has_question and not has_messages:
            raise ValueError("Provide either question or messages.")
        return self


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
    try:
        if req.messages:
            if req.messages[-1].role != "user":
                raise HTTPException(
                    status_code=400,
                    detail="The latest message must be from the user.",
                )
            latest = req.messages[-1].content.strip()
            if not latest:
                raise HTTPException(status_code=400, detail="Question cannot be empty.")
            history = [
                {"role": m.role, "content": m.content.strip()}
                for m in req.messages
                if m.content.strip()
            ]
            result = ask_with_messages(history)
        else:
            question = (req.question or "").strip()
            if not question:
                raise HTTPException(status_code=400, detail="Question cannot be empty.")
            result = ask(question)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sql=result["sql"],
        row_count=len(result["rows"]),
    )
