"""Shared configuration."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Load .env from project root if present
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cricchat:cricchat@localhost:5432/cricchat",
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "cricchat_knowledge"

RAG_TOP_K = 4
