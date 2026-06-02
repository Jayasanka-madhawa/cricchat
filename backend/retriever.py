"""Retrieve relevant knowledge chunks from Chroma."""

import chromadb

from backend.config import CHROMA_DIR, COLLECTION_NAME, RAG_TOP_K


def retrieve_context(question: str, n: int = RAG_TOP_K) -> str:
    """Return top-k documents concatenated as context for the LLM."""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            "Chroma not built. Run: python rag/01_build_chroma.py"
        )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(query_texts=[question], n_results=n)

    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)
