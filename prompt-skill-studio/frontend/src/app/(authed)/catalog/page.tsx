"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api";
import type { CatalogEntry, CatalogKind, Vendor } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn, formatRelative } from "@/lib/utils";

const KINDS: { id: CatalogKind | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "model", label: "Models" },
  { id: "feature", label: "Features" },
  { id: "beta", label: "Beta" },
  { id: "technique", label: "Techniques" },
];

const VENDORS: { id: Vendor | "all"; label: string }[] = [
  { id: "all", label: "All vendors" },
  { id: "anthropic", label: "Anthropic" },
  { id: "openai", label: "OpenAI" },
];

export default function CatalogPage() {
  const [kind, setKind] = useState<CatalogKind | "all">("all");
  const [vendor, setVendor] = useState<Vendor | "all">("all");

  const q = useQuery({
    queryKey: ["catalog", "entries", kind, vendor],
    queryFn: () => {
      const params = new URLSearchParams();
      if (kind !== "all") params.set("kind", kind);
      if (vendor !== "all") params.set("vendor", vendor);
      params.set("limit", "500");
      return request<CatalogEntry[]>(`/catalog/entries?${params.toString()}`);
    },
  });

  return (
    <div className="p-6 space-y-5 max-w-6xl">
      <header>
        <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Vendor catalog</div>
        <h1 className="text-2xl font-semibold tracking-tight">What&apos;s available right now</h1>
        <p className="text-fg-muted mt-1 text-sm">
          The studio polls each vendor&apos;s <span className="font-mono">llms.txt</span> and
          changelog feeds every 6 hours. Entries here reflect the most recent successful capture.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {VENDORS.map((v) => (
          <Button
            key={v.id}
            size="sm"
            variant={vendor === v.id ? "default" : "outline"}
            onClick={() => setVendor(v.id)}
          >
            {v.label}
          </Button>
        ))}
        <span className="w-px self-stretch bg-border mx-1" />
        {KINDS.map((k) => (
          <Button
            key={k.id}
            size="sm"
            variant={kind === k.id ? "default" : "outline"}
            onClick={() => setKind(k.id)}
          >
            {k.label}
          </Button>
        ))}
      </div>

      {q.isLoading && <div className="text-sm text-fg-muted">Loading…</div>}
      {q.error && <div className="text-sm text-danger">Failed to load catalog.</div>}

      <div className="grid gap-3 md:grid-cols-2">
        {(q.data ?? []).map((e) => (
          <Card key={`${e.vendor}-${e.slug}`}>
            <CardHeader className="flex flex-row items-start gap-3 pb-2">
              <Badge tone={e.vendor === "anthropic" ? "brand" : "success"}>{e.vendor}</Badge>
              <Badge>{e.kind}</Badge>
              <span className="text-[11px] text-fg-subtle ml-auto">
                {formatRelative(e.captured_at)}
              </span>
            </CardHeader>
            <CardContent className="pt-0">
              <CardTitle className="font-mono text-sm">{e.slug}</CardTitle>
              <CardDescription className="mt-1">{e.name}</CardDescription>
              {e.props?.description ? (
                <p className="text-sm text-fg-muted mt-2 line-clamp-3">
                  {String(e.props.description)}
                </p>
              ) : null}
              {e.source_url ? (
                <a
                  className="inline-block mt-2 text-xs text-brand hover:underline truncate max-w-full"
                  href={e.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {e.source_url}
                </a>
              ) : null}
            </CardContent>
          </Card>
        ))}
        {(q.data ?? []).length === 0 && !q.isLoading && (
          <div className={cn("col-span-full surface p-6 text-sm text-fg-muted")}>
            No entries yet. Trigger a sync from the worker (
            <span className="font-mono">python -m app.jobs.sync_vendor_docs</span>) or wait for
            the cron service.
          </div>
        )}
      </div>
    </div>
  );
}
