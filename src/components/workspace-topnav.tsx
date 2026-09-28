import { Link, useParams } from "@tanstack/react-router";
import { ClipboardList, FileUp, MessagesSquare, ScrollText, Settings } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { canAdmin, canSteward, useApp } from "@/lib/app-state";
import type { Role } from "@/lib/types";
import { cn } from "@/lib/utils";

const linkClass =
  "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium text-muted-foreground hover:bg-accent hover:text-foreground";
const activeClass = "bg-accent text-foreground";

export function WorkspaceTopNav() {
  const { workspaceId } = useParams({ strict: false }) as { workspaceId?: string };
  const { role, setRole, workspaces, conflicts } = useApp();
  const ws = workspaces.find((w) => w.id === workspaceId);
  const open = conflicts.filter(
    (c) => c.workspaceId === workspaceId && (c.status === "needs_review" || c.status === "escalated"),
  ).length;

  if (!workspaceId) return null;

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background px-4">
      <div className="mr-2 min-w-0">
        <p className="truncate text-sm font-semibold">{ws?.name ?? "Workspace"}</p>
        <p className="text-[11px] text-muted-foreground">{ws?.documentCount ?? 0} documents indexed</p>
      </div>

      <nav className="flex items-center gap-0.5">
        <Link
          to="/workspace/$workspaceId"
          params={{ workspaceId }}
          activeOptions={{ exact: true }}
          className={linkClass}
          activeProps={{ className: cn(linkClass, activeClass) }}
        >
          <MessagesSquare className="size-4" /> Chat
        </Link>
        {canSteward(role) && (
          <>
            <Link
              to="/workspace/$workspaceId/ingestion"
              params={{ workspaceId }}
              className={linkClass}
              activeProps={{ className: cn(linkClass, activeClass) }}
            >
              <FileUp className="size-4" /> Ingestion
            </Link>
            <Link
              to="/workspace/$workspaceId/conflicts"
              params={{ workspaceId }}
              className={linkClass}
              activeProps={{ className: cn(linkClass, activeClass) }}
            >
              <ClipboardList className="size-4" /> Conflicts
              {open > 0 && (
                <span className="ml-0.5 rounded-full bg-warning px-1.5 text-[10px] font-semibold text-warning-foreground">
                  {open}
                </span>
              )}
            </Link>

            <Link
              to="/workspace/$workspaceId/audit-log"
              params={{ workspaceId }}
              className={linkClass}
              activeProps={{ className: cn(linkClass, activeClass) }}
            >
              <ScrollText className="size-4" /> Audit log
            </Link>
          </>
        )}
        {canAdmin(role) && (
          <Link to="/settings" className={linkClass} activeProps={{ className: cn(linkClass, activeClass) }}>
            <Settings className="size-4" /> Settings
          </Link>
        )}
      </nav>

      <div className="ml-auto flex items-center gap-2">
        <span className="text-[11px] text-muted-foreground">Demo role</span>
        <Select value={role} onValueChange={(v) => setRole(v as Role)}>
          <SelectTrigger className="h-8 w-[128px] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="analyst">Analyst</SelectItem>
            <SelectItem value="steward">Steward</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
        <ThemeToggle />
      </div>
    </header>
  );
}
