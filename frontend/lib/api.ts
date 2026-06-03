import type { AnalyzeRequest, AnalyzeResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<AnalyzeResponse>;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
