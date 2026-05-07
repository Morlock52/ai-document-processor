"use client";

import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api";
import type { ChangeEntry } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { formatRelative } from "@/lib/utils";

export default function DiffPage() {
  const q = useQuery({
    queryKey: ["catalog", "changes", "all"],
    queryFn: () => request<ChangeEntry[]>("/catalog/changes?limit=100"),
  });

  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <header>
        <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Change feed</div>
        <h1 className="text-2xl font-semibold tracking-tight">What changed in vendor docs</h1>
        <p className="text-fg-muted mt-1 text-sm">
          Each row is one fetch by the doc-sync job. Diff is a unified diff against the previous
          successful capture of the same URL.
        </p>
      </header>

      {q.isLoading && <div className="text-sm text-fg-muted">Loading…</div>}

      <div className="space-y-3">
        {(q.data ?? []).map((c, i) => (
          <article key={i} className="surface p-4">
            <header className="flex items-center gap-3 mb-2">
              <Badge tone={c.vendor === "anthropic" ? "brand" : "success"}>{c.vendor}</Badge>
              <Badge tone={c.status_code === 200 ? "success" : "warning"}>{c.status_code}</Badge>
              <span className="font-mono text-xs truncate">{c.source_url}</span>
              <span className="ml-auto text-xs text-fg-muted whitespace-nowrap">
                {formatRelative(c.fetched_at)}
              </span>
            </header>
            {c.summary && <div className="text-sm text-fg-muted">{c.summary}</div>}
            {c.diff && (
              <pre className="mt-2 max-h-64 overflow-auto text-xs font-mono p-3 rounded bg-bg-muted border border-border whitespace-pre-wrap">
                {c.diff}
              </pre>
            )}
          </article>
        ))}
        {(q.data ?? []).length === 0 && !q.isLoading && (
          <div className="surface p-6 text-sm text-fg-muted">No fetches recorded yet.</div>
        )}
      </div>
    </div>
  );
}
