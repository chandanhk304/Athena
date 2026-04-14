"use client";

import { useEffect, useState } from "react";
import { ScrollText, RefreshCw } from "lucide-react";
import { getATL } from "@/lib/api";
import type { ATLEntry } from "@/lib/types";

interface ATLPanelProps {
  newEntries?: ATLEntry[]; // pushed from ChatPanel via parent
}

const STATUS_CLASSES: Record<string, string> = {
  LOGGED:           "status-logged",
  PENDING_APPROVAL: "status-pending",
  EXECUTED:         "status-executed",
  REJECTED:         "status-rejected",
};

const ACTION_ICONS: Record<string, string> = {
  TEST_ENTRY:             "🧪",
  BLOCKED_TICKET:         "🚫",
  RISK_DETECTED:          "⚠️",
  EXECUTED_UPDATE:        "✅",
  EXECUTED_ASSIGN:        "👤",
  ACTION_REJECTED:        "❌",
  PENDING_APPROVAL:       "⏸️",
};

function getIcon(actionType: string): string {
  for (const [key, icon] of Object.entries(ACTION_ICONS)) {
    if (actionType.includes(key)) return icon;
  }
  return "📋";
}

export default function ATLPanel({ newEntries = [] }: ATLPanelProps) {
  const [entries, setEntries] = useState<ATLEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [mounted, setMounted] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await getATL();
      setEntries(data);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, []);

  // Merge newly pushed entries from ChatPanel immediately (no wait for next poll)
  useEffect(() => {
    if (newEntries.length === 0) return;
    setEntries((prev) => {
      const existingIds = new Set(prev.map((e) => e.id));
      const fresh = newEntries.filter((e) => !existingIds.has(e.id));
      return [...fresh, ...prev];
    });
  }, [newEntries]);

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        style={{ borderBottom: "1px solid var(--border)", padding: "12px 16px" }}
        className="flex items-center justify-between flex-shrink-0"
      >
        <div className="flex items-center gap-2">
          <ScrollText size={14} style={{ color: "#8b5cf6" }} />
          <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "0.85rem" }}>
            Action Log (ATL)
          </span>
          {entries.length > 0 && (
            <span
              style={{
                background: "rgba(139,92,246,0.15)",
                color: "#a78bfa",
                border: "1px solid rgba(139,92,246,0.3)",
                borderRadius: "10px",
                padding: "1px 7px",
                fontSize: "0.65rem",
                fontWeight: 600,
              }}
            >
              {entries.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span style={{ color: "var(--text-muted)", fontSize: "0.65rem" }}>
            {mounted && lastRefresh
              ? lastRefresh.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
              : "--:--:--"}
          </span>
          <button
            onClick={refresh}
            disabled={loading}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0 }}
          >
            <RefreshCw size={12} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          </button>
        </div>
      </div>

      {/* Entry list */}
      <div className="flex-1 overflow-y-auto" style={{ padding: "10px" }}>
        {entries.length === 0 && !loading && (
          <div
            style={{
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.78rem",
              marginTop: "30px",
              lineHeight: 1.8,
            }}
          >
            <ScrollText size={24} style={{ marginBottom: "8px", opacity: 0.3 }} />
            <p>No actions logged yet.</p>
            <p style={{ fontSize: "0.7rem" }}>Agent actions will appear here.</p>
          </div>
        )}

        {entries.map((entry) => (
          <ATLRow key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  );
}

function ATLRow({ entry }: { entry: ATLEntry }) {
  const statusClass = STATUS_CLASSES[entry.status] ?? "status-logged";
  const icon = getIcon(entry.action_type);

  return (
    <div
      className="slide-in"
      style={{
        padding: "8px 10px",
        marginBottom: "6px",
        background: "rgba(255,255,255,0.025)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        transition: "border-color 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2" style={{ minWidth: 0 }}>
          <span style={{ fontSize: "0.85rem", flexShrink: 0 }}>{icon}</span>
          <span
            style={{
              fontSize: "0.72rem",
              fontWeight: 600,
              color: "var(--text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {entry.action_type.replace(/_/g, " ")}
          </span>
        </div>
        <span className={statusClass} style={{ fontSize: "0.62rem", padding: "1px 6px", borderRadius: "4px", whiteSpace: "nowrap", flexShrink: 0 }}>
          {entry.status}
        </span>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "0.73rem",
          color: "var(--text-muted)",
          margin: "4px 0 4px 26px",
          lineHeight: 1.5,
          overflow: "hidden",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
        }}
      >
        {entry.description}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between" style={{ marginLeft: "26px" }}>
        {entry.entity_key && (
          <span
            style={{
              fontSize: "0.65rem",
              background: "rgba(99,102,241,0.12)",
              color: "#818cf8",
              padding: "1px 5px",
              borderRadius: "3px",
              fontFamily: "monospace",
            }}
          >
            {entry.entity_key}
          </span>
        )}
        <span style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginLeft: "auto" }}>
          {new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
