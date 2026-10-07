import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { entities } from "@/lib/mock-data";
import type { Fact } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace/$workspaceId/entity/$entityId")({
  head: () => ({
    meta: [
      { title: "Entity timeline — ChronosGraph" },
      {
        name: "description",
        content: "See every historical version of an entity's facts along a single time axis.",
      },
      { property: "og:title", content: "Entity timeline — ChronosGraph" },
      {
        property: "og:description",
        content: "See every historical version of an entity's facts along a single time axis.",
      },
    ],
  }),
  component: EntityTimeline,
});

const START = new Date("2022-01-01").getTime();
const END = new Date("2027-01-01").getTime();
const SPAN = END - START;

function pct(dateStr: string | null, fallback: number) {
  if (!dateStr) return fallback;
  return ((new Date(dateStr).getTime() - START) / SPAN) * 100;
}

function overlaps(a: Fact, b: Fact) {
  const aFrom = new Date(a.validFrom).getTime();
  const aTo = a.validTo ? new Date(a.validTo).getTime() : END;
  const bFrom = new Date(b.validFrom).getTime();
  const bTo = b.validTo ? new Date(b.validTo).getTime() : END;
  return aFrom < bTo && bFrom < aTo;
}

function EntityTimeline() {
  const { workspaceId, entityId } = Route.useParams();
  const [entity, setEntity] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const { getEntity } = await import("@/lib/api");
        const data = await getEntity(workspaceId, entityId);
        
        // Format facts to match frontend expectations
        const formattedFacts = data.facts.map((f: any) => {
          let state = "valid";
          if (f.valid_to && new Date(f.valid_to) < new Date()) {
            state = "superseded";
          }
          // The API doesn't know about current unresolved conflicts in this endpoint yet, 
          // so we'll just determine 'under_review' via overlaps below if we wanted, 
          // but 'valid'/'superseded' is enough for basic styling.
          
          return {
            id: f.id,
            entityId: data.id,
            statement: f.relation,
            value: f.value || f.relation,
            documentName: f.document_name || "Unknown",
            snippet: f.evidence,
            validFrom: f.valid_from,
            validTo: f.valid_to,
            extractedAt: new Date().toISOString(), // Fallback
            state: state
          };
        });
        
        setEntity({
          ...data,
          facts: formattedFacts
        });
      } catch (err) {
        console.error("Failed to fetch entity", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId, entityId]);

  if (loading) return <div className="p-10 text-sm text-muted-foreground">Loading entity timeline...</div>;
  if (!entity) return <div className="p-10 text-sm text-muted-foreground">Entity not found.</div>;

  const conflicting = new Set<string>();
  entity.facts.forEach((a: Fact, i: number) =>
    entity.facts.forEach((b: Fact, j: number) => {
      if (i < j && a.value !== b.value && overlaps(a, b)) {
        conflicting.add(a.id);
        conflicting.add(b.id);
      }
    }),
  );

  const fact = entity.facts.find((f: Fact) => f.id === selected);
  const years = [2022, 2023, 2024, 2025, 2026, 2027];

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{entity.type}</p>
      <h1 className="text-xl font-semibold tracking-tight">{entity.name}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {entity.facts.length} recorded versions · {conflicting.size > 0 ? `${conflicting.size} overlapping (contradictory) versions` : "no known conflicts"}
      </p>

      <div className="mt-8 rounded-xl border border-border bg-card p-6">
        <div className="relative flex justify-between border-b border-border pb-2 font-mono text-[10px] text-muted-foreground">
          {years.map((y) => (
            <span key={y}>{y}</span>
          ))}
        </div>

        <div className="relative mt-4 space-y-3">
          {entity.facts.map((f: Fact) => {
            const left = pct(f.validFrom, 0);
            const right = pct(f.validTo, 100);
            const isConflict = conflicting.has(f.id);
            return (
              <div key={f.id} className="relative h-12">
                <button
                  onClick={() => setSelected(f.id)}
                  style={{ left: `${left}%`, width: `${Math.max(right - left, 6)}%` }}
                  className={cn(
                    "absolute top-0 h-12 overflow-hidden rounded-md border px-3 py-1.5 text-left text-xs transition",
                    f.state === "valid" && "border-success/50 bg-success/10",
                    f.state === "superseded" && "border-border bg-muted",
                    f.state === "under_review" && "border-warning/60 bg-warning-surface",
                    isConflict && "ring-1 ring-destructive",
                    selected === f.id && "ring-2 ring-primary",
                  )}
                >
                  <span className="block truncate font-semibold">{f.value}</span>
                  <span className="block truncate text-[10px] text-muted-foreground">
                    {f.validFrom} → {f.validTo ?? "present"}
                  </span>
                </button>
              </div>
            );
          })}
        </div>

        {conflicting.size > 0 && (
          <p className="mt-4 flex items-center gap-2 text-[11px] text-destructive">
            <span className="h-px w-6 bg-destructive" /> red outline = overlapping validity windows with
            differing values
          </p>
        )}
      </div>

      {fact && (
        <div className="mt-6 rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">{fact.value}</h2>
          <p className="mt-1 text-xs text-muted-foreground">{fact.statement}</p>
          <p className="mt-3 rounded-lg border border-border bg-muted/30 p-3 text-xs italic">
            “{fact.snippet}”
          </p>
          <dl className="mt-4 grid gap-2 text-[11px] sm:grid-cols-2">
            {[
              ["Source", fact.documentName],
              ["Extracted", new Date(fact.extractedAt).toLocaleString()],
              ["valid_from", fact.validFrom],
              ["valid_to", fact.validTo ?? "open"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="truncate font-medium">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
