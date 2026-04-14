// Athena PMO — Shared TypeScript types

export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  inputType?: string; // 'query' | 'risk_event' | 'general'
}

export interface ATLEntry {
  id: string;
  action_type: string;
  description: string;
  entity_key?: string;
  severity?: string;
  status: "LOGGED" | "PENDING_APPROVAL" | "EXECUTED" | "REJECTED";
  timestamp: string;
  metadata?: Record<string, unknown>;
  source?: "ingestion" | "agent"; // badge label
}

export interface Risk {
  id: string;
  risk_type: string;
  description: string;
  entity_key?: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "ACTIVE" | "PENDING_APPROVAL" | "RESOLVED";
  detected_at: string;
  source: "auto" | "ai"; // ⚡ Auto-Detected vs 🤖 AI Alert
  atl_id?: string; // for approval calls
}

export interface NodeCounts {
  [label: string]: number;
}

export interface MetricsData {
  neo4j_nodes: NodeCounts;
  neo4j_total: number;
  pinecone_vectors: number;
  events_processed: number;
  risks_detected: number;
  last_event?: string;
}

export interface QueryResponse {
  thread_id: string;
  status: "COMPLETE" | "PENDING_APPROVAL";
  response: string;
  atl_entries?: ATLEntry[];
  input_type?: string;
  atl_id?: string;
  pending_action?: Record<string, unknown>;
}

export interface ChatThread {
  id: string;
  created_at: string;
  preview: string; // first message text
}
