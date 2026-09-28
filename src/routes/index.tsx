import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { FileText, Plus, TriangleAlert } from "lucide-react";
import { useEffect } from "react";
import { Wordmark } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { roleLabel, useApp } from "@/lib/app-state";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Workspaces — ChronosGraph" },
      {
        name: "description",
        content: "Pick a ChronosGraph workspace to query documents and review temporal conflicts.",
      },
      { property: "og:title", content: "Workspaces — ChronosGraph" },
      {
        property: "og:description",
        content: "Pick a ChronosGraph workspace to query documents and review temporal conflicts.",
      },
    ],
  }),
  component: WorkspacePicker,
});

function WorkspacePicker() {
  const { hydrated, user, workspaces, conflicts, lastWorkspaceId, setLastWorkspaceId, createWorkspace, logout } =
    useApp();
  const navigate = useNavigate();

  useEffect(() => {
    if (!hydrated) return;
    if (!user) navigate({ to: "/login" });
    else if (lastWorkspaceId && workspaces.some((w) => w.id === lastWorkspaceId))
      navigate({ to: "/workspace/$workspaceId", params: { workspaceId: lastWorkspaceId } });
  }, [hydrated, user, lastWorkspaceId, workspaces, navigate]);

  if (!hydrated || !user) return null;

  const open = (id: string) =>
    conflicts.filter(
      (c) => c.workspaceId === id && (c.status === "needs_review" || c.status === "escalated"),
    ).length;

  const create = async () => {
    const name = window.prompt("Workspace name");
    if (!name) return;
    const ws = await createWorkspace(name);
    setLastWorkspaceId(ws.id);
    navigate({ to: "/workspace/$workspaceId", params: { workspaceId: ws.id } });
  };

  return (
    <main className="min-h-screen bg-muted/30">
      <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
        <Wordmark />
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            {user.name} · {roleLabel[user.role]}
          </span>
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={() => { logout(); navigate({ to: "/login" }); }}>
            Log out
          </Button>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-12">
        <h1 className="text-2xl font-semibold tracking-tight">Your workspaces</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Each workspace is an isolated temporal knowledge graph over its own document corpus.
        </p>

        {user.role === "pending" && (
          <div className="mt-6 rounded-lg border border-warning/40 bg-warning-surface px-4 py-3 text-sm text-warning-foreground">
            Your account is pending access. An admin needs to assign a role and workspaces before you
            can query documents. Use the demo role switcher inside a workspace to explore.
          </div>
        )}

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces
            .filter((w) => !w.archived)
            .map((ws) => (
              <Link
                key={ws.id}
                to="/workspace/$workspaceId"
                params={{ workspaceId: ws.id }}
                onClick={() => setLastWorkspaceId(ws.id)}
                className="group rounded-xl border border-border bg-card p-5 transition hover:border-primary/50 hover:shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <h2 className="font-semibold tracking-tight">{ws.name}</h2>
                  {open(ws.id) > 0 && (
                    <span className="flex items-center gap-1 rounded-full bg-warning-surface px-2 py-0.5 text-[11px] font-medium text-warning-foreground">
                      <TriangleAlert className="size-3" /> {open(ws.id)}
                    </span>
                  )}
                </div>
                <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{ws.description}</p>
                <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <FileText className="size-3.5" /> {ws.documentCount} documents
                </p>
              </Link>
            ))}

          <button
            onClick={create}
            className="flex min-h-[148px] flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card/50 text-sm text-muted-foreground transition hover:border-primary/50 hover:text-foreground"
          >
            <Plus className="size-5" /> Create new workspace
          </button>
        </div>
      </div>
    </main>
  );
}
