import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useMemo, useState, useEffect } from "react";
import { Slider } from "@/components/ui/slider";
import { useApp } from "@/lib/app-state";
import { apiFetch } from "@/lib/api";
import { entities, graphFor } from "@/lib/mock-data";
import type { GraphNode } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace/$workspaceId/conflicts/$conflictId")({
  head: () => ({
    meta: [
      { title: "Conflict inspector — ChronosGraph" },
      {
        name: "description",
        content: "Inspect a contradiction as a graph of facts with their validity windows.",
      },
      { property: "og:title", content: "Conflict inspector — ChronosGraph" },
      {
        property: "og:description",
        content: "Inspect a contradiction as a graph of facts with their validity windows.",
      },
    ],
  }),
  component: ConflictInspector,
});

const MIN_YEAR = 2022;
const MAX_YEAR = 2027;

function stateColor(state: GraphNode["state"]) {
  if (state === "valid") return "fill-success stroke-success";
  if (state === "superseded") return "fill-destructive stroke-destructive";
  return "fill-muted-foreground stroke-muted-foreground";
}

function activeAt(node: GraphNode, year: number) {
  if (node.kind === "entity") return true;
  const from = node.validFrom ? new Date(node.validFrom).getFullYear() : MIN_YEAR;
  const to = node.validTo ? new Date(node.validTo).getFullYear() : MAX_YEAR;
  return year >= from && year <= to;
}

function ConflictInspector() {
  const { workspaceId, conflictId } = Route.useParams();
  const [conflict, setConflict] = useState<any>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch(`/workspaces/${workspaceId}/conflicts/${conflictId}`);
        setConflict(data);
        
        // Format graph data
        const positions = [
          { x: 22, y: 26 },
          { x: 78, y: 26 },
          { x: 50, y: 78 },
          { x: 16, y: 74 },
        ];
        
        const gNodes: GraphNode[] = [
          { id: data.subject_name, label: data.subject_name, kind: "entity", state: "valid", x: 50, y: 14 },
        ];
        
        const gEdges: GraphEdge[] = [];
        
        data.entity_facts.forEach((f: any, i: number) => {
          // simple heuristic for state: if it has valid_to in the past -> superseded. 
          // If it's part of an unresolved conflict -> under_review. else -> valid.
          let state: "valid" | "superseded" | "under_review" = "valid";
          if (f.valid_to && new Date(f.valid_to) < new Date()) {
            state = "superseded";
          } else if (data.status === "needs_review" || data.status === "escalated" || data.status === "pending_review") {
            if (f.id === data.fact1_id || f.id === data.fact2_id) state = "under_review";
          }
          
          gNodes.push({
            id: f.id,
            label: f.value || f.relation,
            kind: "fact",
            state,
            validFrom: f.valid_from,
            validTo: f.valid_to,
            x: positions[i % positions.length]!.x,
            y: positions[i % positions.length]!.y,
            // Stash raw data for the sidebar
            ...f 
          } as any);
          
          gEdges.push({
            source: data.subject_name,
            target: f.id,
            kind: "asserts"
          });
        });
        
        gEdges.push({ source: data.fact1_id, target: data.fact2_id, kind: "contradicts" });
        
        setNodes(gNodes);
        setEdges(gEdges);
      } catch (err) {
        console.error("Failed to load conflict", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId, conflictId]);

  const selectedFact = useMemo(() => {
    if (!selected) return null;
    return nodes.find((n) => n.id === selected) as any;
  }, [selected, nodes]);

  if (loading) {
    return <div className="p-10 text-sm text-muted-foreground">Loading conflict data...</div>;
  }

  if (!conflict) {
    return <div className="p-10 text-sm text-muted-foreground">Conflict not found.</div>;
  }

  const pos = (id: string) => nodes.find((n) => n.id === id)!;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-border px-6 py-4">
        <Link
          to="/workspace/$workspaceId/conflicts"
          params={{ workspaceId }}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" /> Queue
        </Link>
        <div>
          <h1 className="text-sm font-semibold">{conflict.subject_name}</h1>
          <p className="text-[11px] text-muted-foreground">
            Conflict {conflict.id} · {((conflict.confidence || 0) * 100).toFixed(0)}% suggestion confidence
          </p>
        </div>
        <Link
          to="/workspace/$workspaceId/entity/$entityId"
          params={{ workspaceId, entityId: conflict.subject_name }}
          className="ml-auto text-xs font-medium text-primary hover:underline"
        >
          Open entity timeline
        </Link>
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="relative flex-1 bg-muted/20">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 size-full">
              {edges.map((e, i) => {
                const s = pos(e.source);
                const t = pos(e.target);
                if (!s || !t) return null;
                return (
                  <line
                    key={i}
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    className={
                      e.kind === "contradicts" ? "stroke-destructive" : "stroke-border"
                    }
                    strokeWidth={e.kind === "contradicts" ? 0.5 : 0.3}
                    strokeDasharray={e.kind === "contradicts" ? "1.5 1" : undefined}
                    vectorEffect="non-scaling-stroke"
                  />
                );
              })}
            </svg>
            {nodes.map((n) => {
              const active = activeAt(n, year);
              return (
                <button
                  key={n.id}
                  onClick={() => setSelected(n.kind === "fact" ? n.id : null)}
                  style={{ left: `${n.x}%`, top: `${n.y}%` }}
                  className={cn(
                    "absolute -translate-x-1/2 -translate-y-1/2 rounded-lg border px-3 py-2 text-xs shadow-sm transition",
                    active ? "opacity-100" : "opacity-30",
                    selected === n.id ? "ring-2 ring-primary" : "",
                    n.kind === "entity"
                      ? "border-primary/50 bg-card font-semibold"
                      : "border-border bg-card",
                  )}
                >
                  <span className="flex items-center gap-2">
                    {n.kind === "fact" && (
                      <svg viewBox="0 0 8 8" className={cn("size-2", stateColor(n.state))}>
                        <circle cx="4" cy="4" r="3.5" />
                      </svg>
                    )}
                    {n.label}
                  </span>
                  {n.kind === "fact" && (
                    <span className="mt-0.5 block font-mono text-[10px] text-muted-foreground">
                      {n.validFrom} → {n.validTo ?? "open"}
                    </span>
                  )}
                </button>
              );
            })}

            <div className="absolute left-4 top-4 flex gap-3 rounded-md border border-border bg-card/90 px-3 py-2 text-[11px]">
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-success" /> currently valid
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-destructive" /> superseded
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-muted-foreground" /> under review
              </span>
            </div>
          </div>

          <div className="border-t border-border px-6 py-4">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Time slider — showing facts active in</span>
              <span className="font-mono text-sm font-semibold text-foreground">{year}</span>
            </div>
            <Slider
              className="mt-3"
              min={MIN_YEAR}
              max={MAX_YEAR}
              step={1}
              value={[year]}
              onValueChange={([v]) => setYear(v ?? year)}
            />
            <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
              <span>{MIN_YEAR}</span>
              <span>{MAX_YEAR}</span>
            </div>
          </div>
        </div>

        <aside className="w-[320px] shrink-0 overflow-y-auto border-l border-border bg-card p-5">
          {selectedFact ? (
            <>
              <h2 className="text-sm font-semibold">{selectedFact.value || "Unknown value"}</h2>
              <p className="mt-1 text-xs text-muted-foreground">{selectedFact.relation}</p>
              <p className="mt-4 rounded-lg border border-border bg-muted/30 p-3 text-xs italic">
                “{selectedFact.evidence}”
              </p>
              <dl className="mt-4 space-y-2 text-[11px]">
                {[
                  ["Source document", selectedFact.document_name],
                  ["valid_from", selectedFact.valid_from],
                  ["valid_to", selectedFact.valid_to ?? "open"],
                  ["State", selectedFact.state.replace("_", " ")],
                  ["Fact ID", selectedFact.id],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3">
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="truncate font-medium">{v}</dd>
                  </div>
                ))}
              </dl>
            </>
          ) : (
            <div>
              <h2 className="text-sm font-semibold">Suggested resolution</h2>
              <p className="mt-2 text-xs text-muted-foreground">{conflict.explanation}</p>
              <p className="mt-6 text-xs text-muted-foreground">
                Select a node to inspect its source snippet, extraction timestamp and metadata.
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
