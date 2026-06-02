"""
Step 3 — Test RAG retrieval.

Goal: see which knowledge chunks match a user question.
      Phase 3 LLM will use these chunks to write SQL.

Run:
    python rag/02_test_retrieval.py "Kohli strike rate in ODI"
    python rag/02_test_retrieval.py "Sangakkara when Mahela at other end"
    python rag/02_test_retrieval.py "Bumrah economy first 6 overs T20"
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import chromadb
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "cricchat_knowledge"


def retrieve(question: str, n: int = 3) -> None:
    if not CHROMA_DIR.exists():
        print("Chroma not built yet. Run: python rag/01_build_chroma.py")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(query_texts=[question], n_results=n)

    print("=" * 60)
    print(f"Question: {question}")
    print("=" * 60)

    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0]), 1
    ):
        print(f"\n--- Chunk {i} (type: {meta.get('type')}, distance: {dist:.3f}) ---")
        # Show first 600 chars
        preview = doc[:600] + ("..." if len(doc) > 600 else "")
        print(preview)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python rag/02_test_retrieval.py "your question"')
        print('Example: python rag/02_test_retrieval.py "Kohli strike rate in ODI"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    retrieve(question)


if __name__ == "__main__":
    main()
