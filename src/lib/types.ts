// Typed data models — shaped to map cleanly onto a future Neo4j / FastAPI backend.

export type Role = "analyst" | "steward" | "admin" | "pending";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  workspaceIds: string[];
  createdAt: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  unresolvedConflicts: number;
  archived?: boolean;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  citations?: Citation[];
  conflicts?: { status: string; explanation: string }[];
}

export interface Chat {
  id: string;
  workspaceId: string;
  title: string;
  archived?: boolean;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface Citation {
  index: number;
  documentId: string;
  documentName: string;
  snippet: string;
  validFrom: string;
  validTo: string | null;
  entityId?: string;
}

export type DocStatus =
  | "queued"
  | "parsing"
  | "extracting"
  | "resolving"
  | "auditing"
  | "complete"
  | "failed";

export interface IngestedDocument {
  id: string;
  workspaceId: string;
  filename: string;
  kind?: string;
  status: string;
  current_stage?: string;
  uploadedAt: string;
  errorReason?: string;
}

export interface Fact {
  id: string;
  entityId: string;
  statement: string;
  value: string;
  documentId: string;
  documentName: string;
  snippet: string;
  validFrom: string;
  validTo: string | null;
  extractedAt: string;
  state: "valid" | "superseded" | "under_review";
}

export interface Entity {
  id: string;
  workspaceId: string;
  name: string;
  type: "policy" | "person" | "organization" | "clause" | "measurement";
  facts: Fact[];
}

export interface Conflict {
  id: string;
  workspaceId: string;
  entityId?: string;
  entityName: string;
  factAId: string;
  factBId: string;
  detectedAt: string;
  suggestion: string;
  confidence: number; // 0..1
  status: "auto_resolved" | "needs_review" | "pending_review" | "escalated" | "accepted" | "overridden";
  resolvedBy?: string;

  // Enriched fields from backend
  factAEvidence?: string;
  factBEvidence?: string;
  factAValidFrom?: string;
  factBValidFrom?: string;
  factAValidTo?: string;
  factBValidTo?: string;
  factADocumentName?: string;
  factBDocumentName?: string;
}

export interface AuditEntry {
  id: string;
  workspaceId: string;
  timestamp: string;
  entityName: string;
  summary: string;
  resolution: "auto" | "human";
  resolvedBy: string;
  status: "resolved" | "escalated" | "pending";
}

export interface GraphNode {
  id: string;
  label: string;
  kind: "entity" | "fact";
  state: "valid" | "superseded" | "under_review";
  validFrom?: string;
  validTo?: string | null;
  x: number;
  y: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: "asserts" | "contradicts" | "supersedes";
}
