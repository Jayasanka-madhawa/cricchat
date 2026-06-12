"use client";

import { FormEvent, useRef, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Message =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      content: string;
      sql?: string;
      rowCount?: number;
      error?: boolean;
    };

type ChatApiMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatApiResponse = {
  question: string;
  answer: string;
  sql: string;
  row_count: number;
};

function toApiMessages(messages: Message[]): ChatApiMessage[] {
  return messages
    .filter((m) => !("error" in m && m.error))
    .map((m) => ({
      role: m.role,
      content: m.content,
    }));
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSql, setShowSql] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function sendQuestion(question: string) {
    const nextMessages: Message[] = [
      ...messages,
      { role: "user", content: question },
    ];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: toApiMessages(nextMessages) }),
      });

      const data = await res.json();

      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : "Something went wrong.";
        setMessages((m) => [
          ...m,
          { role: "assistant", content: detail, error: true },
        ]);
        return;
      }

      const body = data as ChatApiResponse;
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: body.answer,
          sql: body.sql,
          rowCount: body.row_count,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            "Could not reach the API. Is uvicorn running on port 8000?",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    sendQuestion(q);
  }

  function askExample(q: string) {
    if (loading) return;
    setInput("");
    sendQuestion(q);
  }

  return (
    <main>
      <header>
        <h1>CricChat</h1>
        <p>Cricket stats from 21k+ matches — ask in plain English</p>
      </header>

      <div className="messages">
        {messages.length === 0 && (
          <div className="empty">
            <p>Try a question:</p>
            <ul>
              <li>
                <button
                  type="button"
                  className="link"
                  onClick={() =>
                    askExample("Kohli strike rate in ODI")
                  }
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--accent)",
                    cursor: "pointer",
                    padding: 0,
                    font: "inherit",
                    textDecoration: "underline",
                  }}
                >
                  Kohli strike rate in ODI
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() =>
                    askExample(
                      "Sangakkara strike rate when Mahela is non-striker"
                    )
                  }
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--accent)",
                    cursor: "pointer",
                    padding: 0,
                    font: "inherit",
                    textDecoration: "underline",
                  }}
                >
                  Sangakkara + Mahela partnership
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() =>
                    askExample("Bumrah economy in first 6 overs T20")
                  }
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--accent)",
                    cursor: "pointer",
                    padding: 0,
                    font: "inherit",
                    textDecoration: "underline",
                  }}
                >
                  Bumrah T20 powerplay economy
                </button>
              </li>
            </ul>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`bubble ${msg.role}${"error" in msg && msg.error ? " error" : ""}`}
          >
            {msg.content}
            {msg.role === "assistant" &&
              showSql &&
              msg.sql &&
              !msg.error && (
                <>
                  <pre className="sql-block">{msg.sql}</pre>
                  {msg.rowCount !== undefined && (
                    <div className="meta">{msg.rowCount} row(s) returned</div>
                  )}
                </>
              )}
          </div>
        ))}

        {loading && <div className="loading">Thinking…</div>}
        <div ref={bottomRef} />
      </div>

      <div className="options">
        <label>
          <input
            type="checkbox"
            checked={showSql}
            onChange={(e) => setShowSql(e.target.checked)}
          />
          Show SQL used
        </label>
      </div>

      <form onSubmit={onSubmit}>
        <input
          type="text"
          placeholder="Ask a cricket stat question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Ask
        </button>
      </form>
    </main>
  );
}
