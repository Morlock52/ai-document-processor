import axios, { AxiosError, type AxiosRequestConfig } from "axios";

// In the browser we always call the same origin (`/api/v1`) so the session
// cookie is same-origin and the middleware can gate on it. Next rewrites
// `/api/v1/*` to the FastAPI service (see next.config.mjs).
// Server-side code can hit the FastAPI service directly via INTERNAL_API_URL.
export const API_URL =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_URL || "http://localhost:8000/api/v1"
    : "/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  timeout: 30_000,
});

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    // 401 -> bounce to login (browser only)
    if (typeof window !== "undefined" && err.response?.status === 401) {
      const here = window.location.pathname + window.location.search;
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = `/login?next=${encodeURIComponent(here)}`;
      }
    }
    return Promise.reject(err);
  }
);

export async function request<T>(
  path: string,
  init: AxiosRequestConfig = {}
): Promise<T> {
  const res = await api.request<T>({ url: path, ...init });
  return res.data;
}

/**
 * Streams a POST as SSE. The backend emits `event: <name>\ndata: <json>\n\n`.
 * onFrame is called for every parsed frame.
 */
export async function streamPost(
  path: string,
  body: unknown,
  onFrame: (event: string, data: unknown) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    credentials: "include",
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`stream failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const chunk = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      let event = "message";
      const dataLines: string[] = [];
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (dataLines.length === 0) continue;
      const dataStr = dataLines.join("\n");
      let parsed: unknown = dataStr;
      try {
        parsed = JSON.parse(dataStr);
      } catch {
        /* keep as string */
      }
      onFrame(event, parsed);
    }
  }
}
