import type { Conflict, IngestedDocument, Chat, ChatMessage, Citation } from "./types";

export function adaptConflict(apiData: any): Conflict {
  return {
    id: apiData.id,
    workspaceId: apiData.workspace_id || "", 
    entityName: apiData.subject_name,
    factAId: apiData.fact1_id,
    factBId: apiData.fact2_id,
    detectedAt: apiData.resolved_at || new Date().toISOString(), // Fallback if missing
    suggestion: apiData.explanation, // map explanation -> suggestion
    confidence: apiData.confidence,
    status: apiData.status,
    resolvedBy: apiData.resolved_by,
    factAEvidence: apiData.fact1_evidence,
    factBEvidence: apiData.fact2_evidence,
    factAValidFrom: apiData.fact1_valid_from,
    factBValidFrom: apiData.fact2_valid_from,
    factAValidTo: apiData.fact1_valid_to,
    factBValidTo: apiData.fact2_valid_to,
    factADocumentName: apiData.fact1_document_name,
    factBDocumentName: apiData.fact2_document_name,
  };
}

export function adaptDocument(apiData: any): IngestedDocument {
  return {
    id: String(apiData.id),
    workspaceId: String(apiData.workspace_id),
    filename: apiData.filename,
    status: apiData.status,
    current_stage: apiData.current_stage,
    uploadedAt: apiData.created_at || new Date().toISOString(),
  };
}

export function adaptMessage(apiData: any): ChatMessage {
  return {
    id: String(apiData.id),
    role: apiData.role,
    content: apiData.content,
    createdAt: apiData.created_at || new Date().toISOString(),
    citations: apiData.citations_json || [],
    conflicts: apiData.conflict_flags_json || [],
  };
}

export function adaptChat(apiData: any): Chat {
  return {
    id: String(apiData.id),
    workspaceId: String(apiData.workspace_id),
    title: apiData.title,
    updatedAt: apiData.created_at || new Date().toISOString(),
    messages: (apiData.messages || []).map(adaptMessage),
  };
}
