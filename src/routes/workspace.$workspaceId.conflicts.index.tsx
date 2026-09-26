import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, CircleCheck, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useApp } from "@/lib/app-state";
import { apiFetch } from "@/lib/api";
import { adaptConflict } from "@/lib/adapters";
import type { Conflict } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace/$workspaceId/conflicts/")({
  head: () => ({
    meta: [
      { title: "Conflict review queue — ChronosGraph" },
      {
        name: "description",
        content: "Review contradictory facts detected across your document corpus over time.",
      },
      { property: "og:title", content: "Conflict review queue — ChronosGraph" },
      {
        property: "og:description",
        content: "Review contradictory facts detected across your document corpus over time.",
      },
    ],
  }),
  component: ConflictQueue,
});

interface FactInfo {
  id: string;
  value: string;
  snippet: string;
  documentName: string;
  validFrom: string;
  validTo: string | null;
}

function FactPane({ fact, tone }: { fact: FactInfo | undefined; tone: "current" | "other" }) {
  if (!fact) return null;
  return (
    <div
      className={cn(
        "rounded-lg border p-3",
        tone === "current" ? "border-primary/40 bg-primary/5" : "border-border bg-muted/40",
      )}
    >
      <p className="text-sm font-semibold">{fact.value}</p>
      <p className="mt-1 text-xs text-muted-foreground">“{fact.snippet}”</p>
      <dl className="mt-3 space-y-1 text-[11px] text-muted-foreground">
        <div className="flex justify-between gap-2">
          <dt>Source</dt>
          <dd className="truncate font-medium text-foreground">{fact.documentName}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>valid_from</dt>
          <dd className="font-mono">{fact.validFrom}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>valid_to</dt>
          <dd className="font-mono">{fact.validTo ?? "open"}</dd>
        </div>
      </dl>
    </div>
  );
}

function ConflictQueue() {
  const { workspaceId } = Route.useParams();
  const { user, role } = useApp();
  const [list, setList] = useState<Conflict[]>([]);

  const fetchConflicts = useCallback(async () => {
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/conflicts`);
      setList(res.map(adaptConflict));
    } catch (err) {
      console.error("Failed to fetch conflicts", err);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchConflicts();
  }, [fetchConflicts]);

  if (role === "analyst") {
    return <NoAccess />;
  }

  const act = async (c: Conflict, status: Conflict["status"], label: string) => {
    try {
      await apiFetch(`/workspaces/${workspaceId}/conflicts/${c.id}/resolve`, {
        method: "POST",
        body: JSON.stringify({
          status,
          resolved_by: user?.name ?? "unknown",
        }),
      });
      toast.success(`${label} — ${c.entityName}`);
      await fetchConflicts();
    } catch (err) {
      console.error("Failed to resolve conflict", err);
      toast.error("Failed to update conflict status");
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="text-xl font-semibold tracking-tight">Conflict review queue</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {list.filter((c) => c.status === "needs_review").length} item(s) need your review ·{" "}
        {list.filter((c) => c.status === "auto_resolved").length} auto-resolved (still reviewable)
      </p>

      <div className="mt-6 space-y-4">
        {list.length === 0 && (
          <p className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
            No known conflicts in this workspace. The background auditor keeps checking as documents
            arrive.
          </p>
        )}

        {list.map((c) => {
          const a: FactInfo = {
            id: c.factAId,
            value: `${c.entityName} ${c.factADocumentName ? "->" : ""} ...`, // backend payload lacks full relation string, simplify for now
            snippet: c.factAEvidence || "No evidence available",
            documentName: c.factADocumentName || "Unknown",
            validFrom: c.factAValidFrom || "unknown",
            validTo: c.factAValidTo || null,
          };
          const b: FactInfo = {
            id: c.factBId,
            value: `${c.entityName} ${c.factBDocumentName ? "->" : ""} ...`,
            snippet: c.factBEvidence || "No evidence available",
            documentName: c.factBDocumentName || "Unknown",
            validFrom: c.factBValidFrom || "unknown",
            validTo: c.factBValidTo || null,
          };
          
          const needs = c.status === "needs_review" || c.status === "escalated" || c.status === "pending_review";
          return (
            <article key={c.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-sm font-semibold">{c.entityName}</h2>
                {needs ? (
                  <span className="flex items-center gap-1 rounded-full bg-warning-surface px-2 py-0.5 text-[11px] font-medium text-warning-foreground">
                    <TriangleAlert className="size-3" />
                    {c.status === "escalated" ? "Escalated" : "Needs your review"}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 rounded-full bg-success/15 px-2 py-0.5 text-[11px] font-medium text-success">
                    <CircleCheck className="size-3" />
                    {c.status === "auto_resolved" ? "Auto-resolved" : c.status === "accepted" ? "Accepted" : "Overridden"}
                  </span>
                )}
                <span className="ml-auto text-[11px] text-muted-foreground">
                  detected {new Date(c.detectedAt).toLocaleString()}
                </span>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <FactPane fact={a} tone="current" />
                <FactPane fact={b} tone="other" />
              </div>

              <div className="mt-4 rounded-lg border border-border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">Suggested resolution</p>
                <p className="mt-1 text-sm">{c.suggestion}</p>
                <div className="mt-3 flex items-center gap-3">
                  <Progress value={c.confidence * 100} className="h-1.5 w-40" />
                  <span className="font-mono text-xs text-muted-foreground">
                    {(c.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Button size="sm" onClick={() => act(c, "accepted", "Resolution accepted")}>
                  Accept
                </Button>
                <Button size="sm" variant="outline" onClick={() => act(c, "overridden", "Resolution overridden")}>
                  Override
                </Button>
                <Button size="sm" variant="ghost" onClick={() => act(c, "escalated", "Escalated for review")}>
                  Escalate
                </Button>
                <Link
                  to="/workspace/$workspaceId/conflicts/$conflictId"
                  params={{ workspaceId, conflictId: c.id }}
                  className="ml-auto flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                >
                  View full conflict graph <ArrowRight className="size-3.5" />
                </Link>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

export function NoAccess() {
  return (
    <div className="mx-auto max-w-md px-6 py-20 text-center">
      <h1 className="text-lg font-semibold">Steward access required</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Your current role is read-only. Ask an admin for Steward access, or switch the demo role in the
        top bar.
      </p>
    </div>
  );
}
