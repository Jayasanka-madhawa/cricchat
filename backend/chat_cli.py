"""
CLI chat — same pipeline as the API, no server needed.

Run:
    python backend/chat_cli.py "Kohli strike rate in ODI"
    python backend/chat_cli.py   # interactive mode
"""

import sys
from pathlib import Path

# Allow running as script from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.agent import ask


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        _handle(question)
        return

    print("CricChat CLI — type a question or 'quit'")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        _handle(question)


def _handle(question: str) -> None:
    print("\nThinking...")
    try:
        result = ask(question)
    except Exception as e:
        print(f"Error: {e}")
        return

    print(f"\nCricChat: {result['answer']}")
    print(f"\nSQL used:\n{result['sql']}")
    if result["rows"]:
        print(f"Rows returned: {len(result['rows'])}")


if __name__ == "__main__":
    main()
