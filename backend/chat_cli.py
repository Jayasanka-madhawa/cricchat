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

from backend.agent import ask, ask_with_messages


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        _handle([{"role": "user", "content": question}])
        return

    print("CricChat CLI — type a question or 'quit'")
    history: list[dict[str, str]] = []
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
        history.append({"role": "user", "content": question})
        if not _handle(history):
            history.pop()


def _handle(messages: list[dict[str, str]]) -> bool:
    print("\nThinking...")
    try:
        if len(messages) == 1:
            result = ask(messages[0]["content"])
        else:
            result = ask_with_messages(messages)
    except Exception as e:
        print(f"Error: {e}")
        return False

    if len(messages) > 1 and result["question"] != messages[-1]["content"]:
        print(f"\n(understood as: {result['question']})")

    print(f"\nCricChat: {result['answer']}")
    print(f"\nSQL used:\n{result['sql']}")
    if result["rows"]:
        print(f"Rows returned: {len(result['rows'])}")

    messages.append({"role": "assistant", "content": result["answer"]})
    return True


if __name__ == "__main__":
    main()
