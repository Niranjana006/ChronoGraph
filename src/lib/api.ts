const API_URL = (import.meta.env["VITE_API_URL"] as string) || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  if (options.body && !(options.body instanceof URLSearchParams) && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignored
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function getConflicts(workspaceId: string) {
  return apiFetch(`/workspaces/${workspaceId}/conflicts`);
}

export async function getConflict(workspaceId: string, conflictId: string) {
  return apiFetch(`/workspaces/${workspaceId}/conflicts/${conflictId}`);
}

export async function getEntity(workspaceId: string, entityId: string) {
  return apiFetch(`/workspaces/${workspaceId}/entities/${encodeURIComponent(entityId)}`);
}
