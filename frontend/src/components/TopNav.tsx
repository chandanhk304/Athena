"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, Activity } from "lucide-react";
import { getSimulatorHealth } from "@/lib/api";

interface TopNavProps {
  vectorCount?: number;
  neo4jTotal?: number;
  onNewChat: () => void;
}

export default function TopNav({ vectorCount = 0, neo4jTotal = 0, onNewChat }: TopNavProps) {
  const [simOnline, setSimOnline] = useState(false);
  const [coreOnline, setCoreOnline] = useState(false);

  useEffect(() => {
    const check = async () => {
      const sim = await getSimulatorHealth();
      setSimOnline(sim);

      try {
        const res = await fetch("http://localhost:8001/api/v1/health", {
          signal: AbortSignal.timeout(3000),
        });
        setCoreOnline(res.ok);
      } catch {
        setCoreOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav
      style={{
        height: "var(--nav-height)",
        background: "rgba(10, 10, 15, 0.95)",
        borderBottom: "1px solid var(--border)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
      className="flex items-center justify-between px-6 sticky top-0 z-50"
    >
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div
          style={{
            background: "var(--accent-dim)",
            borderRadius: "10px",
            padding: "6px",
            border: "1px solid var(--border-bright)",
          }}
        >
          <BrainCircuit size={18} style={{ color: "var(--accent)" }} />
        </div>
        <div>
          <span
            style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: "1rem", letterSpacing: "-0.02em" }}
          >
            Athena
          </span>
          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginLeft: "6px" }}>
            PMO Intelligence
          </span>
        </div>
      </div>

      {/* Center: Status pills */}
      <div className="flex items-center gap-3">
        <StatusPill label="Agent Brain" online={coreOnline} />
        <StatusPill label="Simulator" online={simOnline} />

        {neo4jTotal > 0 && (
          <div
            style={{
              background: "rgba(99,102,241,0.1)",
              border: "1px solid var(--border-bright)",
              borderRadius: "20px",
              padding: "3px 10px",
              fontSize: "0.72rem",
              color: "#a5b4fc",
            }}
            className="flex items-center gap-1.5"
          >
            <Activity size={11} />
            <span>{neo4jTotal.toLocaleString()} nodes · {vectorCount.toLocaleString()} vectors</span>
          </div>
        )}
      </div>

      {/* Right: New Chat */}
      <button
        onClick={onNewChat}
        style={{
          background: "var(--accent-dim)",
          border: "1px solid var(--border-bright)",
          borderRadius: "8px",
          color: "#a5b4fc",
          padding: "6px 14px",
          fontSize: "0.8rem",
          fontWeight: 500,
          cursor: "pointer",
          transition: "all 0.15s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(99,102,241,0.25)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "var(--accent-dim)";
        }}
      >
        + New Chat
      </button>
    </nav>
  );
}

function StatusPill({ label, online }: { label: string; online: boolean }) {
  return (
    <div
      style={{
        background: online ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
        border: `1px solid ${online ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
        borderRadius: "20px",
        padding: "3px 10px",
        fontSize: "0.72rem",
        color: online ? "#4ade80" : "#f87171",
        display: "flex",
        alignItems: "center",
        gap: "5px",
      }}
    >
      <span
        className={online ? "live-pulse" : ""}
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          background: online ? "#4ade80" : "#f87171",
          display: "inline-block",
        }}
      />
      {label}
    </div>
  );
}
