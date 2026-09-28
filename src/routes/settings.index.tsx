import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { canAdmin, roleLabel, useApp } from "@/lib/app-state";
import { users as seedUsers } from "@/lib/mock-data";
import type { Role } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/settings/")({
  head: () => ({
    meta: [
      { title: "Admin settings — ChronosGraph" },
      {
        name: "description",
        content: "Manage users, roles, workspace access and background auditor health.",
      },
      { property: "og:title", content: "Admin settings — ChronosGraph" },
      {
        property: "og:description",
        content: "Manage users, roles, workspace access and background auditor health.",
      },
    ],
  }),
  component: AdminSettings,
});

const health = [
  { label: "Ingestion queue", value: "4 documents pending", tone: "ok" as const },
  { label: "Background auditor", value: "Last full sweep completed 2 hours ago", tone: "ok" as const },
  { label: "Entity resolution worker", value: "Elevated latency (p95 4.2s)", tone: "warn" as const },
  { label: "Graph store", value: "Connected · 12,481 nodes", tone: "ok" as const },
];

function AdminSettings() {
  const { role, workspaces, createWorkspace, archiveWorkspace } = useApp();
  const [people, setPeople] = useState(seedUsers);

  if (!canAdmin(role)) {
    return (
      <div className="mx-auto max-w-md px-6 py-20 text-center">
        <h1 className="text-lg font-semibold">Admin access required</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Switch the demo role to Admin inside a workspace to view this page.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-6 py-10">
      <section>
        <h1 className="text-xl font-semibold tracking-tight">Users & roles</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Roles are assigned here — users cannot self-select them at signup.
        </p>
        <div className="mt-4 overflow-hidden rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">Email</th>
                <th className="px-4 py-2.5 font-medium">Workspaces</th>
                <th className="px-4 py-2.5 font-medium">Role</th>
              </tr>
            </thead>
            <tbody>
              {people.map((u) => (
                <tr key={u.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 font-medium">{u.name}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{u.email}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {u.workspaceIds.length ? u.workspaceIds.length : "none assigned"}
                  </td>
                  <td className="px-4 py-3">
                    <Select
                      value={u.role}
                      onValueChange={(v) => {
                        setPeople((prev) =>
                          prev.map((p) =>
                            p.id === u.id
                              ? {
                                  ...p,
                                  role: v as Role,
                                  workspaceIds:
                                    v === "pending" ? [] : workspaces.map((w) => w.id),
                                }
                              : p,
                          ),
                        );
                        toast.success(`${u.name} is now ${roleLabel[v as Role]}`);
                      }}
                    >
                      <SelectTrigger className="h-8 w-[150px] text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending access</SelectItem>
                        <SelectItem value="analyst">Analyst</SelectItem>
                        <SelectItem value="steward">Steward</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Workspaces</h2>
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              const name = window.prompt("Workspace name");
              if (name) {
                await createWorkspace(name);
                toast.success(`Workspace “${name}” created`);
              }
            }}
          >
            Create workspace
          </Button>
        </div>
        <div className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {workspaces.map((w) => (
            <div key={w.id} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium">
                  {w.name}
                  {w.archived && (
                    <span className="ml-2 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                      archived
                    </span>
                  )}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {w.documentCount} documents · access: all assigned roles
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto"
                onClick={() => archiveWorkspace(w.id)}
              >
                {w.archived ? "Restore" : "Archive"}
              </Button>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold tracking-tight">System health</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {health.map((h) => (
            <div key={h.label} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "size-2 rounded-full",
                    h.tone === "ok" ? "bg-success" : "bg-warning",
                  )}
                />
                <p className="text-sm font-medium">{h.label}</p>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">{h.value}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
