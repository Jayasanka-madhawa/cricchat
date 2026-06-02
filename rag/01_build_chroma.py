"""
Step 2 — Build Chroma knowledge base from rag/knowledge/*.md

Goal: embed schema docs + SQL examples so the chatbot can retrieve
      relevant context before writing SQL.

Run:
    pip install -r rag/requirements.txt
    python rag/01_build_chroma.py

Output:
    chroma_db/   (local vector database)
"""

import os
import re
import sys
from pathlib import Path

# Keep Chroma model cache inside project (avoids permission issues)
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import chromadb
KNOWLEDGE_DIR = ROOT / "rag" / "knowledge"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "cricchat_knowledge"


def load_documents() -> list[dict]:
    """Load markdown files and split into chunks."""
    docs = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = path.read_text()
        name = path.stem

        # Split sql_examples.md by each ## Example block for better retrieval
        if name == "sql_examples":
            parts = re.split(r"(?=^## Example \d+)", text, flags=re.MULTILINE)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                title = part.split("\n")[0].replace("## ", "")
                docs.append({
                    "id": f"sql_{title.lower().replace(' ', '_')[:50]}",
                    "text": part,
                    "metadata": {"source": name, "type": "sql_example"},
                })
        else:
            docs.append({
                "id": name,
                "text": text,
                "metadata": {"source": name, "type": name},
            })

    return docs


def main() -> None:
    print("=" * 60)
    print("PHASE 2 — Build Chroma knowledge base")
    print("=" * 60)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents from {KNOWLEDGE_DIR}/")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Fresh build — delete old collection if re-running
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   Cleared old collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "CricChat schema, stats, SQL examples"},
    )

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )

    print(f"\n✅ Indexed {len(docs)} documents into Chroma")
    print(f"   Location : {CHROMA_DIR}/")
    print(f"   Collection: {COLLECTION_NAME}")

    print("\nDocument types:")
    types = {}
    for d in docs:
        t = d["metadata"]["type"]
        types[t] = types.get(t, 0) + 1
    for t, n in sorted(types.items()):
        print(f"   {t}: {n}")

    print("\nNext: python rag/02_test_retrieval.py \"Kohli strike rate in ODI\"")


if __name__ == "__main__":
    main()
