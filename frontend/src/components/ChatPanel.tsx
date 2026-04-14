"use client";

import { useEffect, useRef, useState, KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, User, BrainCircuit } from "lucide-react";
import { sendQuery } from "@/lib/api";
import type { Message, ATLEntry } from "@/lib/types";

const STORAGE_MESSAGES_KEY = "athena_messages";
const STORAGE_THREAD_KEY = "athena_thread_id";

interface ChatPanelProps {
  resetKey: number; // increment to trigger new chat
  onNewATLEntries?: (entries: ATLEntry[]) => void;
}

export default function ChatPanel({ resetKey, onNewATLEntries }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | undefined>(undefined);
  const bottomRef = useRef<HTMLDivElement>(null);

  // ── Load persisted conversation ──────────────────────────────
  useEffect(() => {
    if (resetKey === 0) {
      // Initial load — restore from localStorage
      try {
        const saved = localStorage.getItem(STORAGE_MESSAGES_KEY);
        const savedThread = localStorage.getItem(STORAGE_THREAD_KEY);
        if (saved) setMessages(JSON.parse(saved));
        if (savedThread) setThreadId(savedThread);
      } catch { /* ignore parse errors */ }
    } else {
      // New chat requested — wipe state and storage
      setMessages([]);
      setThreadId(undefined);
      setInput("");
      localStorage.removeItem(STORAGE_MESSAGES_KEY);
      localStorage.removeItem(STORAGE_THREAD_KEY);
    }
  }, [resetKey]);

  // ── Persist to localStorage on every message change ──────────
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_MESSAGES_KEY, JSON.stringify(messages));
    }
    if (threadId) {
      localStorage.setItem(STORAGE_THREAD_KEY, threadId);
    }
  }, [messages, threadId]);

  // ── Auto-scroll to newest message ────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Send message ─────────────────────────────────────────────
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendQuery(text, threadId);

      // Persist thread ID from first response
      if (!threadId && response.thread_id) {
        setThreadId(response.thread_id);
      }

      const aiMsg: Message = {
        id: `msg-${Date.now()}-ai`,
        role: "assistant",
        content: response.response || "_No response content._",
        timestamp: new Date().toISOString(),
        inputType: response.input_type,
      };
      setMessages((prev) => [...prev, aiMsg]);

      // Bubble up new ATL entries to parent
      if (response.atl_entries && response.atl_entries.length > 0) {
        onNewATLEntries?.(response.atl_entries);
      }

      // If pending approval, show a system notice
      if (response.status === "PENDING_APPROVAL") {
        const noticeMsg: Message = {
          id: `msg-${Date.now()}-notice`,
          role: "system",
          content: `⏸️ **Human Gate Paused** — Action \`${response.atl_id}\` requires your approval. Check the **Risk Feed** panel.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, noticeMsg]);
      }
    } catch (err) {
      const errMsg: Message = {
        id: `msg-${Date.now()}-err`,
        role: "system",
        content: `❌ Failed to reach Athena Core. Make sure \`uvicorn athena_core.api:app --port 8001\` is running.\n\nError: ${err instanceof Error ? err.message : String(err)}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Panel Header */}
      <div
        style={{ borderBottom: "1px solid var(--border)", padding: "14px 18px" }}
        className="flex items-center justify-between flex-shrink-0"
      >
        <div className="flex items-center gap-2">
          <BrainCircuit size={15} style={{ color: "var(--accent)" }} />
          <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "0.85rem" }}>
            AI Chat
          </span>
          {threadId && (
            <span
              style={{
                color: "var(--text-muted)",
                fontSize: "0.68rem",
                background: "rgba(255,255,255,0.04)",
                padding: "2px 6px",
                borderRadius: "4px",
                fontFamily: "monospace",
              }}
            >
              {threadId.slice(0, 8)}…
            </span>
          )}
        </div>
        <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>
          {messages.length} messages · Shift+Enter for newline
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto" style={{ padding: "16px" }}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full" style={{ color: "var(--text-muted)" }}>
            <BrainCircuit size={40} style={{ marginBottom: "16px", opacity: 0.3 }} />
            <p style={{ fontSize: "0.9rem", fontWeight: 500, marginBottom: "6px" }}>
              Ask Athena anything.
            </p>
            <p style={{ fontSize: "0.8rem", textAlign: "center", maxWidth: "280px", lineHeight: 1.6 }}>
              Try: <em>&quot;What are the blocked tickets?&quot;</em><br />
              or: <em>&quot;Show me the current sprint status.&quot;</em>
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex items-start gap-3 slide-in" style={{ marginBottom: "16px" }}>
            <AvatarIcon role="assistant" />
            <div
              className="glass-card flex items-center gap-1.5"
              style={{ padding: "10px 14px", display: "inline-flex" }}
            >
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="typing-dot"
                  style={{
                    width: "6px", height: "6px", borderRadius: "50%",
                    background: "var(--accent)", display: "inline-block",
                    animationDelay: `${i * 0.15}s`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Box */}
      <div
        style={{ borderTop: "1px solid var(--border)", padding: "12px 16px" }}
        className="flex-shrink-0"
      >
        <div
          className="flex items-end gap-2"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid var(--border)",
            borderRadius: "10px",
            padding: "8px 12px",
            transition: "border-color 0.2s",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--border-bright)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        >
          <textarea
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Athena about your project…"
            rows={1}
            disabled={loading}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              resize: "none",
              color: "var(--text-primary)",
              fontSize: "0.875rem",
              lineHeight: "1.5",
              maxHeight: "100px",
              overflowY: "auto",
            }}
          />
          <button
            id="chat-send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            style={{
              background: input.trim() && !loading ? "var(--accent)" : "rgba(99,102,241,0.2)",
              border: "none",
              borderRadius: "6px",
              padding: "6px",
              cursor: input.trim() && !loading ? "pointer" : "not-allowed",
              color: input.trim() && !loading ? "white" : "var(--text-muted)",
              transition: "all 0.15s ease",
              flexShrink: 0,
            }}
          >
            <Send size={14} />
          </button>
        </div>
        <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "6px", textAlign: "center" }}>
          Powered by Groq Llama 3.3 70B · Neo4j · Pinecone
        </p>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div
        className="slide-in"
        style={{
          margin: "8px 0 16px 0",
          padding: "10px 14px",
          background: "rgba(99,102,241,0.08)",
          border: "1px solid var(--border-bright)",
          borderRadius: "8px",
          fontSize: "0.8rem",
          color: "#a5b4fc",
        }}
      >
        <span className="md-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </span>
      </div>
    );
  }

  return (
    <div
      className={`flex items-start gap-3 slide-in ${isUser ? "flex-row-reverse" : ""}`}
      style={{ marginBottom: "16px" }}
    >
      <AvatarIcon role={message.role} />
      <div
        style={{
          maxWidth: "85%",
          background: isUser
            ? "rgba(99,102,241,0.18)"
            : "rgba(255,255,255,0.04)",
          border: `1px solid ${isUser ? "rgba(99,102,241,0.3)" : "var(--border)"}`,
          borderRadius: isUser ? "12px 2px 12px 12px" : "2px 12px 12px 12px",
          padding: "10px 14px",
        }}
      >
        {isUser ? (
          <p style={{ fontSize: "0.875rem", margin: 0, color: "var(--text-primary)", lineHeight: 1.6 }}>
            {message.content}
          </p>
        ) : (
          <div className="md-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
        <div
          style={{
            fontSize: "0.65rem",
            color: "var(--text-muted)",
            marginTop: "4px",
            textAlign: isUser ? "left" : "right",
            display: "flex",
            gap: "6px",
            justifyContent: isUser ? "flex-start" : "flex-end",
            alignItems: "center",
          }}
        >
          {message.inputType && (
            <span
              style={{
                background: "rgba(99,102,241,0.15)",
                color: "#818cf8",
                padding: "1px 5px",
                borderRadius: "3px",
                fontSize: "0.62rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {message.inputType}
            </span>
          )}
          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}

function AvatarIcon({ role }: { role: string }) {
  const isUser = role === "user";
  return (
    <div
      style={{
        width: "28px",
        height: "28px",
        borderRadius: "50%",
        background: isUser ? "rgba(99,102,241,0.2)" : "rgba(34,197,94,0.15)",
        border: `1px solid ${isUser ? "rgba(99,102,241,0.4)" : "rgba(34,197,94,0.3)"}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      {isUser ? (
        <User size={13} style={{ color: "#a5b4fc" }} />
      ) : (
        <BrainCircuit size={13} style={{ color: "#4ade80" }} />
      )}
    </div>
  );
}
