import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as mock from "./mock-data";
import { apiFetch, setToken, clearToken, getToken } from "./api";
import type { Chat, ChatMessage, Conflict, Role, User, Workspace } from "./types";

const STORAGE_KEY = "chronosgraph.session.v1";

interface Session {
  user: User | null;
  lastWorkspaceId: string | null;
}

interface AppState {
  hydrated: boolean;
  user: User | null;
  role: Role;
  login: (email: string, password?: string) => Promise<{ ok: boolean; error?: string }>;
  signup: (name: string, email: string, password?: string) => Promise<{ ok: boolean; error?: string }>;
  logout: () => void;
  setRole: (role: Role) => void;
  updateUser: (patch: Partial<User>) => void;
  lastWorkspaceId: string | null;
  setLastWorkspaceId: (id: string) => void;
  workspaces: Workspace[];
  fetchWorkspaces: () => Promise<void>;
  createWorkspace: (name: string) => Promise<Workspace>;
  archiveWorkspace: (id: string) => void;
  chats: Chat[];
  createChat: (workspaceId: string) => Promise<Chat>;
  renameChat: (id: string, title: string) => void;
  deleteChat: (id: string) => void;
  archiveChat: (id: string) => void;
  appendMessages: (chatId: string, messages: ChatMessage[]) => void;
  conflicts: Conflict[];
  setConflictStatus: (id: string, status: Conflict["status"], by: string) => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [hydrated, setHydrated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [lastWorkspaceId, setLastWs] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [chats, setChats] = useState<Chat[]>(mock.chats);
  const [conflicts, setConflicts] = useState<Conflict[]>(mock.conflicts);

  useEffect(() => {
    async function hydrateUser() {
      try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as Session;
          setLastWs(parsed.lastWorkspaceId ?? null);
        }
        if (getToken()) {
          const me = await apiFetch("/auth/me");
          const account: User = {
            id: String(me.id),
            name: me.name,
            email: me.email,
            role: (me.role as Role) || "analyst",
            workspaceIds: [],
            createdAt: me.created_at,
          };
          setUser(account);
        }
      } catch {
        clearToken();
        setUser(null);
      } finally {
        setHydrated(true);
      }
    }
    hydrateUser();
  }, []);

  const persist = useCallback((next: Session) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }, []);

  const login: AppState["login"] = useCallback(
    async (email, password = "") => {
      try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        
        const res = await apiFetch("/auth/login", {
          method: "POST",
          body: formData,
        });
        
        setToken(res.access_token);
        
        // Fetch real user details and role from backend /auth/me
        const me = await apiFetch("/auth/me");
        const account: User = {
          id: String(me.id),
          name: me.name,
          email: me.email,
          role: (me.role as Role) || "analyst",
          workspaceIds: [],
          createdAt: me.created_at,
        };
        setUser(account);
        persist({ user: account, lastWorkspaceId });
        return { ok: true };
      } catch (err: any) {
        return { ok: false, error: err.message || "Failed to log in" };
      }
    },
    [lastWorkspaceId, persist],
  );

  const signup: AppState["signup"] = useCallback(
    async (name, email, password = "") => {
      try {
        await apiFetch("/auth/signup", {
          method: "POST",
          body: JSON.stringify({ name, email, password }),
        });
        
        // Auto login after signup
        const loginRes = await login(email, password);
        return loginRes;
      } catch (err: any) {
        return { ok: false, error: err.message || "Failed to sign up" };
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    persist({ user: null, lastWorkspaceId: null });
  }, [persist]);

  const setRole = useCallback(
    (role: Role) => {
      // Role is read from real backend authentication/profile; manual override disabled.
      console.warn("Manual role override is disabled. Role is assigned by backend.");
    },
    [],
  );

  const updateUser = useCallback(
    (patch: Partial<User>) => {
      setUser((prev) => {
        if (!prev) return prev;
        const next = { ...prev, ...patch };
        persist({ user: next, lastWorkspaceId });
        return next;
      });
    },
    [lastWorkspaceId, persist],
  );

  const setLastWorkspaceId = useCallback(
    (id: string) => {
      setLastWs(id);
      if (hydrated) persist({ user, lastWorkspaceId: id });
    },
    [hydrated, persist, user],
  );

  const fetchWorkspaces = useCallback(async () => {
    try {
      if (!user) return;
      const res = await apiFetch("/workspaces");
      const list = await Promise.all(
        res.map(async (w: any) => {
          let count = 0;
          try {
            const docs = await apiFetch(`/workspaces/${w.id}/documents`);
            count = docs.length;
          } catch {
            /* ignore fallback */
          }
          return {
            id: String(w.id),
            name: w.name,
            description: "Workspace",
            documentCount: count,
            unresolvedConflicts: 0,
            updatedAt: w.created_at,
          };
        }),
      );
      setWorkspaces(list);
    } catch (err) {
      console.error("Failed to fetch workspaces", err);
    }
  }, [user]);

  useEffect(() => {
    if (user && hydrated) {
      fetchWorkspaces();
    }
  }, [user, hydrated, fetchWorkspaces]);

  const createWorkspace = useCallback(async (name: string) => {
    const res = await apiFetch("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name, description: "New workspace" })
    });
    const ws: Workspace = {
      id: String(res.id),
      name: res.name,
      description: "New workspace — no documents ingested yet.",
      documentCount: 0,
      unresolvedConflicts: 0,
      updatedAt: res.created_at,
    };
    setWorkspaces((prev) => [...prev, ws]);
    return ws;
  }, []);

  const archiveWorkspace = useCallback((id: string) => {
    setWorkspaces((prev) => prev.map((w) => (w.id === id ? { ...w, archived: !w.archived } : w)));
  }, []);

  const createChat = useCallback(async (workspaceId: string) => {
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/chats`, { 
        method: "POST",
        body: JSON.stringify({ title: "New chat" })
      });
      const chat: Chat = {
        id: String(res.id),
        workspaceId,
        title: "New chat",
        updatedAt: new Date().toISOString(),
        messages: [],
      };
      setChats((prev) => [chat, ...prev]);
      return chat;
    } catch (err) {
      console.error("Failed to create chat", err);
      throw err;
    }
  }, []);

  const renameChat = useCallback((id: string, title: string) => {
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, title } : c)));
  }, []);

  const deleteChat = useCallback((id: string) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const archiveChat = useCallback((id: string) => {
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, archived: !c.archived } : c)));
  }, []);

  const appendMessages = useCallback((chatId: string, messages: ChatMessage[]) => {
    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              title:
                c.messages.length === 0 && messages[0]?.role === "user"
                  ? messages[0].content.slice(0, 40)
                  : c.title,
              updatedAt: new Date().toISOString(),
              messages: [...c.messages, ...messages],
            }
          : c,
      ),
    );
  }, []);

  const setConflictStatus = useCallback(
    (id: string, status: Conflict["status"], by: string) => {
      setConflicts((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status, resolvedBy: by } : c)),
      );
    },
    [],
  );

  const value = useMemo<AppState>(
    () => ({
      hydrated,
      user,
      role: user?.role ?? "pending",
      login,
      signup,
      logout,
      setRole,
      updateUser,
      lastWorkspaceId,
      setLastWorkspaceId,
      workspaces,
      fetchWorkspaces,
      createWorkspace,
      archiveWorkspace,
      chats,
      createChat,
      renameChat,
      deleteChat,
      archiveChat,
      appendMessages,
      conflicts,
      setConflictStatus,
    }),
    [
      hydrated,
      user,
      login,
      signup,
      logout,
      setRole,
      updateUser,
      lastWorkspaceId,
      setLastWorkspaceId,
      workspaces,
      fetchWorkspaces,
      createWorkspace,
      archiveWorkspace,
      chats,
      createChat,
      renameChat,
      deleteChat,
      archiveChat,
      appendMessages,
      conflicts,
      setConflictStatus,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp must be used within AppStateProvider");
  return ctx;
}

export const roleLabel: Record<Role, string> = {
  analyst: "Analyst",
  steward: "Steward",
  admin: "Admin",
  pending: "Pending access",
};

export function canSteward(role: Role) {
  return role === "steward" || role === "admin";
}
export function canAdmin(role: Role) {
  return role === "admin";
}
