import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { NoAccess } from "./workspace.$workspaceId.conflicts.index";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useApp } from "@/lib/app-state";
import { apiFetch } from "@/lib/api";
import type { AuditEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/workspace/$workspaceId/audit-log")({
  head: () => ({
    meta: [
      { title: "Audit log — ChronosGraph" },
      {
        name: "description",
        content: "Every conflict resolution, who made it, and whether it was automatic or human.",
      },
      { property: "og:title", content: "Audit log — ChronosGraph" },
      {
        property: "og:description",
        content: "Every conflict resolution, who made it, and whether it was automatic or human.",
      },
    ],
  }),
  component: AuditLog,
});

function AuditLog() {
  const { workspaceId } = Route.useParams();
  const { role, workspaces } = useApp();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [resolution, setResolution] = useState("all");
  const [scope, setScope] = useState(workspaceId);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const targetWs = scope === "all" ? workspaceId : scope;
    apiFetch(`/workspaces/${targetWs}/audit-log`)
      .then((data) => {
        if (!cancelled) {
          setEntries(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load audit log entries", err);
        if (!cancelled) {
          setEntries([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId, scope]);

  const rows = useMemo(
    () =>
      entries.filter((e) => {
        if (scope !== "all" && e.workspaceId !== scope) return false;
        if (resolution !== "all" && e.resolution !== resolution) return false;
        if (from && new Date(e.timestamp) < new Date(from)) return false;
        if (to && new Date(e.timestamp) > new Date(to)) return false;
        const needle = q.trim().toLowerCase();
        if (!needle) return true;
        return (
          e.entityName.toLowerCase().includes(needle) ||
          e.summary.toLowerCase().includes(needle) ||
          e.resolvedBy.toLowerCase().includes(needle)
        );
      }),
    [entries, q, resolution, scope, from, to],
  );

  if (role === "analyst") return <NoAccess />;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-xl font-semibold tracking-tight">Audit log</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        A permanent record of how each contradiction was resolved.
      </p>

      <div className="mt-6 grid gap-2 sm:grid-cols-5">
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search entity, summary, user"
          className="h-9 sm:col-span-2"
        />
        <Select value={scope} onValueChange={setScope}>
          <SelectTrigger className="h-9 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All workspaces</SelectItem>
            {workspaces.map((w) => (
              <SelectItem key={w.id} value={w.id}>
                {w.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={resolution} onValueChange={setResolution}>
          <SelectTrigger className="h-9 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any resolution</SelectItem>
            <SelectItem value="auto">Auto</SelectItem>
            <SelectItem value="human">Human</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex gap-2">
          <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="h-9 text-xs" />
          <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="h-9 text-xs" />
        </div>
      </div>

      <div className="mt-6 overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5 font-medium">Timestamp</th>
              <th className="px-4 py-2.5 font-medium">Entity</th>
              <th className="px-4 py-2.5 font-medium">Conflicting facts</th>
              <th className="px-4 py-2.5 font-medium">Resolution</th>
              <th className="px-4 py-2.5 font-medium">Resolved by</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                  {new Date(e.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 font-medium">{e.entityName}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{e.summary}</td>
                <td className="px-4 py-3 text-xs capitalize">{e.resolution}</td>
                <td className="px-4 py-3 text-xs">{e.resolvedBy}</td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[11px] font-medium",
                      e.status === "resolved" && "bg-success/15 text-success",
                      e.status === "pending" && "bg-warning-surface text-warning-foreground",
                      e.status === "escalated" && "bg-danger-surface text-destructive",
                    )}
                  >
                    {e.status}
                  </span>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No entries match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
