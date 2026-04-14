"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, Zap, Bot } from "lucide-react";
import { getRisks, submitApproval } from "@/lib/api";
import type { Risk } from "@/lib/types";

const SEVERITY_CONFIG = {
  CRITICAL: { class: "badge-critical", label: "CRITICAL", dot: "#ef4444" },
  HIGH:     { class: "badge-high",     label: "HIGH",     dot: "#f97316" },
  MEDIUM:   { class: "badge-medium",   label: "MEDIUM",   dot: "#eab308" },
  LOW:      { class: "badge-low",      label: "LOW",      dot: "#22c55e" },
};

export default function RiskFeed() {
  const [risks, setRisks] = useState<Risk[]>([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [mounted, setMounted] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getRisks();
      setRisks(data);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleApproval = async (risk: Risk, action: "APPROVE" | "REJECT") => {
    const id = risk.atl_id ?? risk.id;
    setApproving(risk.id);
    try {
      await submitApproval(id, action);
      // Optimistic update: mark as resolved locally
      setRisks((prev) =>
        prev.map((r) =>
          r.id === risk.id ? { ...r, status: "RESOLVED" } : r
        )
      );
      // Full refresh after 1.5s to get server state
      setTimeout(refresh, 1500);
    } catch (err) {
      console.error("Approval failed:", err);
    } finally {
      setApproving(null);
    }
  };

  const activeRisks = risks.filter((r) => r.status !== "RESOLVED");
  const resolvedCount = risks.filter((r) => r.status === "RESOLVED").length;

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        style={{ borderBottom: "1px solid var(--border)", padding: "12px 16px" }}
        className="flex items-center justify-between flex-shrink-0"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle size={14} style={{ color: "var(--risk-high)" }} />
          <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "0.85rem" }}>
            Risk Feed
          </span>
          {activeRisks.length > 0 && (
            <span
              style={{
                background: "rgba(239,68,68,0.15)",
                color: "#f87171",
                border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: "10px",
                padding: "1px 7px",
                fontSize: "0.65rem",
                fontWeight: 700,
              }}
              className="live-pulse"
            >
              {activeRisks.length} active
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

      {/* Source legend */}
      <div
        style={{
          padding: "8px 14px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          gap: "12px",
          flexShrink: 0,
        }}
      >
        <LegendPill icon={<Zap size={10} />} label="Auto-Detected" color="#f97316" />
        <LegendPill icon={<Bot size={10} />} label="AI Alert" color="var(--accent)" />
        {resolvedCount > 0 && (
          <span style={{ fontSize: "0.67rem", color: "var(--text-muted)", marginLeft: "auto" }}>
            {resolvedCount} resolved
          </span>
        )}
      </div>

      {/* Risk cards */}
      <div className="flex-1 overflow-y-auto" style={{ padding: "10px" }}>
        {activeRisks.length === 0 && !loading && (
          <div style={{ textAlign: "center", color: "var(--text-muted)", marginTop: "40px" }}>
            <CheckCircle size={28} style={{ color: "var(--risk-low)", marginBottom: "10px", opacity: 0.7 }} />
            <p style={{ fontSize: "0.85rem", fontWeight: 500, color: "#4ade80" }}>All clear</p>
            <p style={{ fontSize: "0.75rem" }}>No active risks detected.</p>
          </div>
        )}

        {activeRisks.map((risk) => (
          <RiskCard
            key={risk.id}
            risk={risk}
            onApprove={() => handleApproval(risk, "APPROVE")}
            onReject={() => handleApproval(risk, "REJECT")}
            isProcessing={approving === risk.id}
          />
        ))}
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────

function RiskCard({
  risk,
  onApprove,
  onReject,
  isProcessing,
}: {
  risk: Risk;
  onApprove: () => void;
  onReject: () => void;
  isProcessing: boolean;
}) {
  const sev = SEVERITY_CONFIG[risk.severity] ?? SEVERITY_CONFIG.HIGH;
  const isPending = risk.status === "PENDING_APPROVAL";

  return (
    <div
      className="slide-in"
      style={{
        marginBottom: "10px",
        padding: "12px",
        background: "rgba(255,255,255,0.025)",
        border: `1px solid ${isPending ? "rgba(234,179,8,0.3)" : "var(--border)"}`,
        borderRadius: "10px",
        borderLeft: `3px solid ${sev.dot}`,
        transition: "all 0.2s ease",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.025)")}
    >
      {/* Top row: severity + source badge */}
      <div className="flex items-center justify-between" style={{ marginBottom: "6px" }}>
        <div className="flex items-center gap-2">
          <span className={sev.class} style={{ fontSize: "0.62rem", padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
            {sev.label}
          </span>
          <SourceBadge source={risk.source} />
        </div>
        {isPending && (
          <span
            style={{
              fontSize: "0.62rem",
              color: "#fbbf24",
              background: "rgba(234,179,8,0.1)",
              border: "1px solid rgba(234,179,8,0.3)",
              borderRadius: "4px",
              padding: "1px 6px",
              fontWeight: 600,
            }}
            className="live-pulse"
          >
            ⏸ AWAITING APPROVAL
          </span>
        )}
      </div>

      {/* Risk type */}
      <p
        style={{
          fontSize: "0.72rem",
          fontWeight: 600,
          color: "var(--text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          marginBottom: "4px",
        }}
      >
        {risk.risk_type.replace(/_/g, " ")}
      </p>

      {/* Description */}
      <p
        style={{
          fontSize: "0.78rem",
          color: "var(--text-primary)",
          lineHeight: 1.5,
          marginBottom: "8px",
          overflow: "hidden",
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
        }}
      >
        {risk.description}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {risk.entity_key && (
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
              {risk.entity_key}
            </span>
          )}
          <span style={{ fontSize: "0.62rem", color: "var(--text-muted)" }}>
            {new Date(risk.detected_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {/* Approve / Reject buttons — only for PENDING_APPROVAL */}
        {isPending && (
          <div className="flex items-center gap-2">
            <ActionButton
              id={`reject-${risk.id}`}
              label="Reject"
              icon={<XCircle size={12} />}
              onClick={onReject}
              disabled={isProcessing}
              color="var(--risk-critical)"
              bg="rgba(239,68,68,0.1)"
              borderColor="rgba(239,68,68,0.3)"
            />
            <ActionButton
              id={`approve-${risk.id}`}
              label="Approve"
              icon={<CheckCircle size={12} />}
              onClick={onApprove}
              disabled={isProcessing}
              color="var(--risk-low)"
              bg="rgba(34,197,94,0.1)"
              borderColor="rgba(34,197,94,0.3)"
            />
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({
  id, label, icon, onClick, disabled, color, bg, borderColor,
}: {
  id: string; label: string; icon: React.ReactNode; onClick: () => void;
  disabled: boolean; color: string; bg: string; borderColor: string;
}) {
  return (
    <button
      id={id}
      onClick={onClick}
      disabled={disabled}
      style={{
        background: bg,
        border: `1px solid ${borderColor}`,
        borderRadius: "6px",
        color,
        padding: "4px 10px",
        fontSize: "0.72rem",
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        display: "flex",
        alignItems: "center",
        gap: "4px",
        transition: "all 0.15s ease",
      }}
    >
      {icon}
      {disabled ? "…" : label}
    </button>
  );
}

function SourceBadge({ source }: { source: "auto" | "ai" }) {
  return source === "auto" ? (
    <span
      style={{
        fontSize: "0.6rem",
        background: "rgba(249,115,22,0.1)",
        color: "#fb923c",
        border: "1px solid rgba(249,115,22,0.25)",
        borderRadius: "3px",
        padding: "1px 5px",
        display: "flex",
        alignItems: "center",
        gap: "3px",
      }}
    >
      <Zap size={9} /> Auto-Detected
    </span>
  ) : (
    <span
      style={{
        fontSize: "0.6rem",
        background: "rgba(99,102,241,0.1)",
        color: "#a5b4fc",
        border: "1px solid rgba(99,102,241,0.25)",
        borderRadius: "3px",
        padding: "1px 5px",
        display: "flex",
        alignItems: "center",
        gap: "3px",
      }}
    >
      <Bot size={9} /> AI Alert
    </span>
  );
}

function LegendPill({ icon, label, color }: { icon: React.ReactNode; label: string; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px", color, fontSize: "0.67rem" }}>
      {icon}
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
    </div>
  );
}
