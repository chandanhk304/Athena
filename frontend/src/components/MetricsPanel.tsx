"use client";

import { useEffect, useState } from "react";
import { BarChart3, Database, Search, Layers, RefreshCw, AlertTriangle } from "lucide-react";
import { getMetrics, getVectorCount } from "@/lib/api";
import type { MetricsData } from "@/lib/types";

interface MetricsPanelProps {
  onMetricsLoaded?: (neo4jTotal: number, vectors: number) => void;
}

const NODE_ICONS: Record<string, string> = {
  Task: "🎯", User: "👤", Project: "📁", Epic: "🗺️",
  Sprint: "🏃", Risk: "⚠️", Comment: "💬",
};

const NODE_COLORS: Record<string, string> = {
  Task: "var(--accent)", User: "#06b6d4", Project: "#8b5cf6",
  Epic: "#f97316", Sprint: "#22c55e", Risk: "#ef4444", Comment: "#94a3b8",
};

export default function MetricsPanel({ onMetricsLoaded }: MetricsPanelProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [vectorCount, setVectorCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [mounted, setMounted] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [m, v] = await Promise.all([getMetrics(), getVectorCount()]);
      setMetrics(m);
      setVectorCount(v);
      setLastRefresh(new Date());
      onMetricsLoaded?.(m.neo4j_total, v);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        style={{ borderBottom: "1px solid var(--border)", padding: "12px 16px" }}
        className="flex items-center justify-between flex-shrink-0"
      >
        <div className="flex items-center gap-2">
          <BarChart3 size={14} style={{ color: "var(--accent)" }} />
          <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "0.85rem" }}>
            Metrics
          </span>
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

      <div className="flex-1 overflow-y-auto" style={{ padding: "14px" }}>
        {/* Store summary pills */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "14px" }}>
          <StorePill
            icon={<Database size={13} />}
            label="Neo4j Nodes"
            value={metrics?.neo4j_total ?? 0}
            color="var(--accent)"
          />
          <StorePill
            icon={<Search size={13} />}
            label="Pinecone Vectors"
            value={vectorCount}
            color="#06b6d4"
          />
          <StorePill
            icon={<Layers size={13} />}
            label="Events Processed"
            value={metrics?.events_processed ?? 0}
            color="#8b5cf6"
          />
          <StorePill
            icon={<AlertTriangle size={13} />}
            label="Risks Detected"
            value={metrics?.risks_detected ?? 0}
            color="var(--risk-high)"
          />
        </div>

        {/* Neo4j node breakdown */}
        {metrics?.neo4j_nodes && Object.keys(metrics.neo4j_nodes).length > 0 && (
          <>
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em" }}>
              Knowledge Graph Breakdown
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {Object.entries(metrics.neo4j_nodes)
                .sort(([, a], [, b]) => b - a)
                .map(([label, count]) => (
                  <NodeBar
                    key={label}
                    label={label}
                    count={count}
                    total={metrics.neo4j_total}
                    color={NODE_COLORS[label] ?? "var(--text-muted)"}
                    icon={NODE_ICONS[label] ?? "📌"}
                  />
                ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!loading && !metrics && (
          <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "20px" }}>
            <AlertTriangle size={24} style={{ marginBottom: "8px", opacity: 0.5 }} />
            <p>Could not load metrics.</p>
            <p style={{ fontSize: "0.72rem" }}>Is Athena Core running on :8001?</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StorePill({
  icon, label, value, color,
}: {
  icon: React.ReactNode; label: string; value: number; color: string;
}) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "10px 12px",
      }}
    >
      <div className="flex items-center gap-1.5" style={{ color, marginBottom: "4px" }}>
        {icon}
        <span style={{ fontSize: "0.68rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {label}
        </span>
      </div>
      <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
        {value.toLocaleString()}
      </div>
    </div>
  );
}

function NodeBar({
  label, count, total, color, icon,
}: {
  label: string; count: number; total: number; color: string; icon: string;
}) {
  const pct = total > 0 ? Math.max(4, (count / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between" style={{ marginBottom: "3px" }}>
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "5px" }}>
          <span>{icon}</span> {label}
        </span>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
          {count.toLocaleString()}
        </span>
      </div>
      <div style={{ height: "4px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: color,
            borderRadius: "2px",
            opacity: 0.7,
            transition: "width 0.5s ease",
          }}
        />
      </div>
    </div>
  );
}
