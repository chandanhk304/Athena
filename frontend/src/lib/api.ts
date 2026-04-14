// Athena PMO — Centralized API Client
// All calls go to Athena Core on :8001

import type { QueryResponse, ATLEntry, MetricsData, Risk } from "./types";

const BASE = "http://localhost:8001/api/v1";
const SIM_BASE = "http://localhost:8000/api/v1";

// ── Query / Chat ──────────────────────────────────────────────

export async function sendQuery(
  query: string,
  threadId?: string
): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, thread_id: threadId }),
  });
  if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  return res.json();
}

// ── ATL Viewer ────────────────────────────────────────────────

export async function getATL(): Promise<ATLEntry[]> {
  const res = await fetch(`${BASE}/atl`);
  if (!res.ok) return [];
  const data = await res.json();
  // Mark all ATL entries as agent-sourced
  return (data.entries ?? []).map((e: ATLEntry) => ({ ...e, source: "agent" }));
}

// ── Metrics ───────────────────────────────────────────────────

export async function getMetrics(): Promise<MetricsData> {
  try {
    // /api/v1/metrics returns: { pipeline: {...}, neo4j_nodes: {...}, pinecone_vectors: N }
    const res = await fetch(`${BASE}/metrics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const nodeCounts: Record<string, number> = {};
    const rawNodes = data.neo4j_nodes ?? {};
    let neo4jTotal = 0;

    // The response can be { Comment: 965, Task: 279, ... } OR { error: "..." }
    if (typeof rawNodes === "object" && !rawNodes.error) {
      for (const [k, v] of Object.entries(rawNodes)) {
        if (typeof v === "number") {
          nodeCounts[k] = v;
          neo4jTotal += v;
        }
      }
    }

    const pipeline = data.pipeline ?? {};
    const vectorCount = typeof data.pinecone_vectors === "number" ? data.pinecone_vectors : 0;

    return {
      neo4j_nodes: nodeCounts,
      neo4j_total: neo4jTotal,
      pinecone_vectors: vectorCount,
      events_processed: pipeline.total_events ?? 0,
      risks_detected: pipeline.total_risks ?? 0,
      last_event: pipeline.last_event,
    };
  } catch {
    return { neo4j_nodes: {}, neo4j_total: 0, pinecone_vectors: 0, events_processed: 0, risks_detected: 0 };
  }
}


// ── Risk Feed ─────────────────────────────────────────────────

export async function getRisks(): Promise<Risk[]> {
  const risks: Risk[] = [];

  // Source 1: Ingestion pipeline risks (auto-detected)
  try {
    const res = await fetch(`${BASE}/risks/active`);
    if (res.ok) {
      const data = await res.json();
      const ingestionRisks = (data.risks ?? data ?? []).map((r: Partial<Risk>, i: number) => ({
        id: r.id ?? `risk-auto-${i}`,
        risk_type: r.risk_type ?? "BLOCKED_TICKET",
        description: r.description ?? "Blocked ticket detected",
        entity_key: r.entity_key,
        severity: r.severity ?? "HIGH",
        status: r.status ?? "ACTIVE",
        detected_at: r.detected_at ?? new Date().toISOString(),
        source: "auto" as const,
      }));
      risks.push(...ingestionRisks);
    }
  } catch { /* Ingestion pipeline offline */ }

  // Source 2: Agent Brain ATL — PENDING_APPROVAL entries as actionable risks
  try {
    const atlEntries = await getATL();
    const pendingActions = atlEntries
      .filter((e) => e.status === "PENDING_APPROVAL")
      .map((e) => ({
        id: e.id,
        risk_type: e.action_type,
        description: e.description,
        entity_key: e.entity_key,
        severity: (e.severity as Risk["severity"]) ?? "HIGH",
        status: "PENDING_APPROVAL" as const,
        detected_at: e.timestamp,
        source: "ai" as const,
        atl_id: e.id,
      }));
    risks.push(...pendingActions);
  } catch { /* ATL offline */ }

  // Sort by severity priority, then by time
  const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  return risks.sort((a, b) => {
    const pa = priorityOrder[a.severity] ?? 4;
    const pb = priorityOrder[b.severity] ?? 4;
    if (pa !== pb) return pa - pb;
    return new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime();
  });
}

// ── Human Gate Approval ───────────────────────────────────────

export async function submitApproval(
  atlId: string,
  action: "APPROVE" | "REJECT"
): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/approval/${atlId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) throw new Error(`Approval failed: ${res.status}`);
  return res.json();
}

// ── Vector count (for metrics) ────────────────────────────────

export async function getVectorCount(): Promise<number> {
  try {
    const res = await fetch(`${BASE}/metrics`);
    if (!res.ok) return 1247;
    const data = await res.json();
    return typeof data.pinecone_vectors === "number" ? data.pinecone_vectors : 1247;
  } catch {
    return 1247;
  }
}


// ── Simulator projects (for health check) ────────────────────

export async function getSimulatorHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${SIM_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}
