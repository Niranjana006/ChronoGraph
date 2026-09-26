import { Link, useNavigate } from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronRight,
  Clock,
  FileText,
  SendHorizonal,
  SlidersHorizontal,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApp } from "@/lib/app-state";
import { promptSuggestions } from "@/lib/mock-data";
import type { Chat, ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";

import { apiFetch } from "@/lib/api";
import { adaptMessage } from "@/lib/adapters";

function formatWindow(from: string, to: string | null) {
  return `${from} → ${to ?? "present"}`;
}


export function ChatView({ workspaceId, chat }: { workspaceId: string; chat: Chat | null }) {
  const { appendMessages, createChat, conflicts } = useApp();
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [pending, setPending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const messages = useMemo(() => chat?.messages ?? [], [chat]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, pending]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [chat?.id]);

  const send = async (text: string) => {
    const content = text.trim();
    if (!content) return;
    let targetId = chat?.id;
    if (!targetId) {
      const created = await createChat(workspaceId);
      targetId = created.id;
      navigate({
        to: "/workspace/$workspaceId/chat/$chatId",
        params: { workspaceId, chatId: created.id },
      });
    }
    const userMsg: ChatMessage = {
      id: `m-${Date.now()}-u`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };
    appendMessages(targetId, [userMsg]);
    setDraft("");
    setPending(true);
    
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/chats/${targetId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      appendMessages(targetId, [adaptMessage(res)]);
    } catch (err) {
      console.error("Failed to send message", err);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col px-6">
      <div className="flex-1 space-y-6 py-8">
        {messages.length === 0 && !pending && (
          <div className="py-16 text-center">
            <h1 className="text-xl font-semibold tracking-tight">Ask about this corpus</h1>
            <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
              Answers cite the source documents and their validity windows, and flag facts with known
              contradictions.
            </p>
            <div className="mx-auto mt-6 grid max-w-lg gap-2">
              {promptSuggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-lg border border-border bg-card px-4 py-2.5 text-left text-sm hover:border-primary/50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                {m.content}
              </div>
            </div>
          ) : (
            <AnswerCard key={m.id} message={m} workspaceId={workspaceId} conflictTitles={conflicts} />
          ),
        )}

        {pending && (
          <p className="animate-pulse text-sm text-muted-foreground">
            Retrieving facts and auditing the affected neighborhood…
          </p>
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 bg-background pb-6">
        <button
          onClick={() => setShowFilters((s) => !s)}
          className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
        >
          <SlidersHorizontal className="size-3.5" /> Retrieval filters
          {showFilters ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
        </button>
        {showFilters && (
          <div className="mb-2 grid gap-2 rounded-lg border border-border bg-card p-3 sm:grid-cols-3">
            <div>
              <label className="text-[11px] text-muted-foreground">Valid from</label>
              <Input type="date" className="h-8 text-xs" />
            </div>
            <div>
              <label className="text-[11px] text-muted-foreground">Source type</label>
              <Input placeholder="PDF, DOCX, XLSX" className="h-8 text-xs" />
            </div>
            <div>
              <label className="text-[11px] text-muted-foreground">Entity type</label>
              <Input placeholder="policy, clause, person" className="h-8 text-xs" />
            </div>
          </div>
        )}
        <div className="flex items-end gap-2 rounded-xl border border-border bg-card p-2">
          <Textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(draft);
              }
            }}
            rows={1}
            placeholder="Ask a question about these documents…"
            className="min-h-9 resize-none border-0 bg-transparent px-2 py-1.5 text-sm shadow-none focus-visible:ring-0"
          />
          <Button size="icon" onClick={() => send(draft)} disabled={!draft.trim()} aria-label="Send">
            <SendHorizonal className="size-4" />
          </Button>
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Answers reflect current best evidence in the graph and may be incomplete.
        </p>
      </div>
    </div>
  );
}

function AnswerCard({
  message,
  workspaceId,
  conflictTitles,
}: {
  message: ChatMessage;
  workspaceId: string;
  conflictTitles: ReturnType<typeof useApp>["conflicts"];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>

      {message.conflicts && message.conflicts.map((conflict, i) => {
        return (
          <div
            key={i}
            className="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-warning/40 bg-warning-surface px-3 py-2 text-xs text-warning-foreground"
          >
            <TriangleAlert className="size-4 shrink-0" />
            <span className="font-medium">
              Conflicting information exists for this fact ({conflict.status})
            </span>
            <Link
              to="/workspace/$workspaceId/conflicts"
              params={{ workspaceId }}
              className="ml-auto font-semibold underline underline-offset-2"
            >
              View details
            </Link>
          </div>
        );
      })}

      {message.citations && message.citations.length > 0 && (
        <div className="mt-4 border-t border-border pt-3">
          <button
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            {open ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
            Evidence & timeline ({message.citations.length} sources)
          </button>
          {open && (
            <ul className="mt-3 space-y-2">
              {message.citations.map((c: any, i: number) => (
                <li key={c.index || i} className="rounded-lg border border-border bg-background p-3">
                  <div className="flex items-center gap-2 text-xs font-medium">
                    <span className="flex size-5 items-center justify-center rounded bg-accent text-[10px]">
                      {c.index || (i + 1)}
                    </span>
                    <FileText className="size-3.5 text-muted-foreground" />
                    {c.documentName || c.document_name}
                  </div>
                  <p className="mt-1.5 text-xs text-muted-foreground">“{c.snippet || c.evidence}”</p>
                  <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="size-3" /> {formatWindow(c.validFrom || c.valid_from || "Unknown", c.validTo || c.valid_to || null)}
                    </span>
                    {c.entityId && (
                      <Link
                        to="/workspace/$workspaceId/entity/$entityId"
                        params={{ workspaceId, entityId: c.entityId }}
                        className={cn("text-primary hover:underline")}
                      >
                        View entity timeline
                      </Link>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
