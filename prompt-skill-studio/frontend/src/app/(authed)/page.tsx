"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, RefreshCw } from "lucide-react";
import { request } from "@/lib/api";
import type { CatalogEntry, ChangeEntry } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatRelative } from "@/lib/utils";

export default function Dashboard() {
  const models = useQuery({
    queryKey: ["catalog", "models"],
    queryFn: () => request<CatalogEntry[]>("/catalog/entries?kind=model&limit=20"),
  });
  const changes = useQuery({
    queryKey: ["catalog", "changes"],
    queryFn: () => request<ChangeEntry[]>("/catalog/changes?limit=10"),
  });

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <header className="flex items-end justify-between gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Dashboard</div>
          <h1 className="text-2xl font-semibold tracking-tight">Prompt &amp; Skill Studio</h1>
          <p className="text-fg-muted mt-1 text-sm">
            Author prompts, Anthropic Skills, OpenAI Agents SDK specs, and MCP server stubs —
            grounded in the latest vendor guidance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <Link href="/catalog">
              Browse catalog <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild>
            <Link href="/studio/prompts">New prompt</Link>
          </Button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Latest models</CardTitle>
              <Badge tone="brand">Live</Badge>
            </div>
            <CardDescription>
              Pulled from each vendor&apos;s <span className="font-mono">llms.txt</span> on the
              last sync.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {models.isLoading && <div className="text-sm text-fg-muted">Loading…</div>}
            {models.error && (
              <div className="text-sm text-danger">Could not load model catalog.</div>
            )}
            <ul className="divide-y divide-border -mx-2">
              {(models.data ?? []).slice(0, 12).map((m) => (
                <li key={`${m.vendor}-${m.slug}`} className="px-2 py-2 flex items-center gap-3">
                  <Badge tone={m.vendor === "anthropic" ? "brand" : "success"}>{m.vendor}</Badge>
                  <span className="font-mono text-sm">{m.slug}</span>
                  <span className="text-fg-muted text-sm truncate">{m.name}</span>
                </li>
              ))}
              {(models.data ?? []).length === 0 && !models.isLoading && (
                <li className="px-2 py-3 text-sm text-fg-muted">
                  No catalog yet — run the doc-sync job (worker &amp; cron services).
                </li>
              )}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent doc-sync activity</CardTitle>
              <RefreshCw className="h-4 w-4 text-fg-muted" />
            </div>
            <CardDescription>
              The cron service polls vendor docs every 6 hours.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border -mx-2">
              {(changes.data ?? []).slice(0, 8).map((c, i) => (
                <li key={i} className="px-2 py-2 flex items-center gap-3">
                  <Badge tone={c.status_code === 200 ? "success" : "warning"}>
                    {c.status_code}
                  </Badge>
                  <span className="font-mono text-xs truncate">{c.source_url}</span>
                  <span className="text-fg-muted text-xs ml-auto whitespace-nowrap">
                    {formatRelative(c.fetched_at)}
                  </span>
                </li>
              ))}
              {(changes.data ?? []).length === 0 && !changes.isLoading && (
                <li className="px-2 py-3 text-sm text-fg-muted">
                  No sync runs yet — check the worker logs.
                </li>
              )}
            </ul>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          {
            title: "Prompts",
            href: "/studio/prompts",
            blurb: "System + user templates with variables and technique presets.",
          },
          {
            title: "Skills",
            href: "/studio/skills",
            blurb: "SKILL.md authoring with Anthropic frontmatter validation. Export ZIP.",
          },
          {
            title: "Agents & MCP",
            href: "/studio/agents",
            blurb: "OpenAI Agents SDK specs and MCP server scaffolds.",
          },
        ].map((c) => (
          <Card key={c.href}>
            <CardHeader>
              <CardTitle>{c.title}</CardTitle>
              <CardDescription>{c.blurb}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" size="sm">
                <Link href={c.href}>
                  Open <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
