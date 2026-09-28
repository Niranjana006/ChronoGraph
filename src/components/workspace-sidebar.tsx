import { Link, useNavigate, useParams } from "@tanstack/react-router";
import {
  Archive,
  ChevronDown,
  ChevronRight,
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Wordmark } from "@/components/brand";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { roleLabel, useApp } from "@/lib/app-state";
import { cn } from "@/lib/utils";

export function WorkspaceSidebar() {
  const {
    workspaces,
    chats,
    conflicts,
    user,
    createWorkspace,
    createChat,
    renameChat,
    deleteChat,
    archiveChat,
    setLastWorkspaceId,
  } = useApp();
  const params = useParams({ strict: false }) as { workspaceId?: string; chatId?: string };
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return workspaces
      .filter((w) => !w.archived)
      .map((w) => {
        const wsChats = chats.filter((c) => c.workspaceId === w.id && !c.archived);
        if (!q) return { ws: w, chats: wsChats };
        const nameHit = w.name.toLowerCase().includes(q);
        const hits = wsChats.filter(
          (c) =>
            c.title.toLowerCase().includes(q) ||
            c.messages.some((m) => m.content.toLowerCase().includes(q)),
        );
        return nameHit || hits.length ? { ws: w, chats: nameHit ? wsChats : hits } : null;
      })
      .filter(Boolean) as { ws: (typeof workspaces)[number]; chats: typeof chats }[];
  }, [workspaces, chats, query]);

  const unresolved = (wsId: string) =>
    conflicts.filter(
      (c) => c.workspaceId === wsId && (c.status === "needs_review" || c.status === "escalated"),
    ).length;

  const handleNewWorkspace = async () => {
    const name = window.prompt("Workspace name");
    if (!name) return;
    const ws = await createWorkspace(name);
    setLastWorkspaceId(ws.id);
    navigate({ to: "/workspace/$workspaceId", params: { workspaceId: ws.id } });
  };

  const handleNewChat = (workspaceId: string) => {
    const chat = createChat(workspaceId);
    navigate({
      to: "/workspace/$workspaceId/chat/$chatId",
      params: { workspaceId, chatId: chat.id },
    });
  };

  return (
    <aside className="flex h-full w-[272px] shrink-0 flex-col border-r border-border bg-sidebar">
      <div className="flex items-center justify-between px-4 py-3.5">
        <Link to="/">
          <Wordmark />
        </Link>
      </div>

      <div className="px-3 pb-2">
        <Button variant="outline" size="sm" className="w-full justify-start gap-2" onClick={handleNewWorkspace}>
          <Plus className="size-4" /> New workspace
        </Button>
      </div>

      <div className="relative px-3 pb-3">
        <Search className="pointer-events-none absolute left-5.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search workspaces & chats"
          className="h-8 pl-8 text-xs"
        />
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 pb-4">
        {visible.map(({ ws, chats: wsChats }) => {
          const open = !collapsed[ws.id];
          const count = unresolved(ws.id);
          return (
            <div key={ws.id}>
              <div
                className={cn(
                  "group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm",
                  params.workspaceId === ws.id ? "bg-accent" : "hover:bg-accent/60",
                )}
              >
                <button
                  onClick={() => setCollapsed((p) => ({ ...p, [ws.id]: open }))}
                  className="text-muted-foreground"
                  aria-label={open ? "Collapse" : "Expand"}
                >
                  {open ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
                </button>
                <Link
                  to="/workspace/$workspaceId"
                  params={{ workspaceId: ws.id }}
                  onClick={() => setLastWorkspaceId(ws.id)}
                  className="flex-1 truncate font-medium"
                >
                  {ws.name}
                </Link>
                {count > 0 && (
                  <span className="flex size-5 items-center justify-center rounded-full bg-destructive text-[10px] font-semibold text-destructive-foreground">
                    {count}
                  </span>
                )}
              </div>

              {open && (
                <div className="mt-0.5 ml-4 space-y-0.5 border-l border-border pl-2">
                  {wsChats.map((chat) => (
                    <div
                      key={chat.id}
                      className={cn(
                        "group flex items-center rounded-md pr-1 text-[13px]",
                        params.chatId === chat.id ? "bg-accent" : "hover:bg-accent/60",
                      )}
                    >
                      <Link
                        to="/workspace/$workspaceId/chat/$chatId"
                        params={{ workspaceId: ws.id, chatId: chat.id }}
                        className="flex-1 truncate px-2 py-1.5 text-muted-foreground hover:text-foreground"
                      >
                        {chat.title}
                      </Link>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            className="opacity-0 transition group-hover:opacity-100"
                            aria-label={`Chat options for ${chat.title}`}
                          >
                            <MoreHorizontal className="size-3.5 text-muted-foreground" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-40">
                          <DropdownMenuItem
                            onClick={() => {
                              const t = window.prompt("Rename chat", chat.title);
                              if (t) renameChat(chat.id, t);
                            }}
                          >
                            <Pencil className="size-3.5" /> Rename
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => archiveChat(chat.id)}>
                            <Archive className="size-3.5" /> Archive
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => {
                              deleteChat(chat.id);
                              if (params.chatId === chat.id)
                                navigate({
                                  to: "/workspace/$workspaceId",
                                  params: { workspaceId: ws.id },
                                });
                            }}
                          >
                            <Trash2 className="size-3.5" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  ))}
                  <button
                    onClick={() => handleNewChat(ws.id)}
                    className="flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-[13px] text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                  >
                    <MessageSquarePlus className="size-3.5" /> New chat
                  </button>
                </div>
              )}
            </div>
          );
        })}
        {visible.length === 0 && (
          <p className="px-3 py-6 text-xs text-muted-foreground">No matches for “{query}”.</p>
        )}
      </nav>

      <Link
        to="/settings/profile"
        className="flex items-center gap-2.5 border-t border-border px-3 py-3 hover:bg-accent/60"
      >
        <span className="flex size-8 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
          {(user?.name ?? "?")
            .split(" ")
            .map((n) => n[0])
            .join("")
            .slice(0, 2)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-medium">{user?.name ?? "Guest"}</span>
          <span className="block text-[11px] text-muted-foreground">
            {roleLabel[user?.role ?? "pending"]}
          </span>
        </span>
      </Link>
    </aside>
  );
}
