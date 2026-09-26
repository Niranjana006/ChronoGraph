import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, FileUp, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { NoAccess } from "./workspace.$workspaceId.conflicts.index";
import { useApp } from "@/lib/app-state";
import { apiFetch } from "@/lib/api";
import { adaptDocument } from "@/lib/adapters";
import type { DocStatus, IngestedDocument } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace/$workspaceId/ingestion")({
  head: () => ({
    meta: [
      { title: "Ingestion dashboard — ChronosGraph" },
      {
        name: "description",
        content: "Track per-document parsing, entity extraction and neighborhood conflict audits.",
      },
      { property: "og:title", content: "Ingestion dashboard — ChronosGraph" },
      {
        property: "og:description",
        content: "Track per-document parsing, entity extraction and neighborhood conflict audits.",
      },
    ],
  }),
  component: IngestionPage,
});

const STAGES: DocStatus[] = ["queued", "parsing", "extracting", "resolving", "auditing", "complete"];

const STATUS_LABEL: Record<DocStatus, string> = {
  queued: "Queued",
  parsing: "Parsing",
  extracting: "Extracting entities",
  resolving: "Resolving against existing graph",
  auditing: "Auditing affected neighborhood",
  complete: "Complete",
  failed: "Failed",
};

function statusClass(s: DocStatus) {
  if (s === "complete") return "bg-success/15 text-success";
  if (s === "failed") return "bg-danger-surface text-destructive";
  if (s === "queued") return "bg-muted text-muted-foreground";
  return "bg-primary/10 text-primary";
}

function IngestionPage() {
  const { workspaceId } = Route.useParams();
  const { role, conflicts } = useApp();
  const [docs, setDocs] = useState<IngestedDocument[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/documents`);
      setDocs(res.map(adaptDocument));
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchDocs();
    const t = window.setInterval(fetchDocs, 3500); // poll every 3.5s
    return () => window.clearInterval(t);
  }, [fetchDocs]);

  const addFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      
      setUploading(true);
      try {
        for (const file of Array.from(files)) {
          if (!file.name.toLowerCase().endsWith(".pdf")) {
            alert(`Only PDF files are supported currently. Skipping ${file.name}`);
            continue;
          }
          
          const formData = new FormData();
          formData.append("file", file);
          
          await apiFetch(`/workspaces/${workspaceId}/documents`, {
            method: "POST",
            body: formData, // fetch will automatically set multipart/form-data boundary
          });
        }
        await fetchDocs();
      } catch (err) {
        console.error("Upload failed", err);
        alert("Upload failed. Check console for details.");
      } finally {
        setUploading(false);
      }
    },
    [workspaceId, fetchDocs],
  );

  if (role === "analyst") return <NoAccess />;

  const newConflicts = conflicts.filter(
    (c) => c.workspaceId === workspaceId && c.status === "needs_review",
  ).length;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="text-xl font-semibold tracking-tight">Ingestion dashboard</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Every upload updates the existing graph incrementally — nothing is rebuilt from scratch.
      </p>

      {newConflicts > 0 && (
        <Link
          to="/workspace/$workspaceId/conflicts"
          params={{ workspaceId }}
          className="mt-5 flex items-center gap-2 rounded-lg border border-warning/40 bg-warning-surface px-4 py-3 text-sm text-warning-foreground hover:brightness-105"
        >
          <TriangleAlert className="size-4" />
          {newConflicts} new contradiction{newConflicts > 1 ? "s" : ""} detected since your last visit
          <ArrowRight className="ml-auto size-4" />
        </Link>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "mt-6 cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition",
          dragging ? "border-primary bg-primary/5" : "border-border bg-card",
        )}
      >
        <FileUp className="mx-auto size-6 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium">
          {uploading ? "Uploading..." : "Drop documents here or click to browse"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">PDF files only (MVP)</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      <div className="mt-8 overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5 font-medium">Filename</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Graph impact</th>
              <th className="px-4 py-2.5 font-medium">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3 font-medium">{d.filename}</td>
                <td className="px-4 py-3">
                  <span
                    title={d.errorReason}
                    className={cn(
                      "inline-block rounded-full px-2 py-0.5 text-[11px] font-medium",
                      statusClass(d.status),
                    )}
                  >
                    {STATUS_LABEL[d.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {d.status === "failed"
                    ? "No changes applied"
                    : d.status === "completed"
                      ? "Graph updated successfully"
                      : d.current_stage
                        ? STATUS_LABEL[d.current_stage as DocStatus] || d.current_stage
                        : "Waiting for a worker"}
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {new Date(d.uploadedAt).toLocaleString()}
                </td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No documents ingested in this workspace yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
