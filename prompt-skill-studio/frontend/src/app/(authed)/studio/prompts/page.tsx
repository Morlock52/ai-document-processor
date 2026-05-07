"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil } from "lucide-react";
import { toast } from "sonner";
import { request } from "@/lib/api";
import type { PromptOut } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatRelative } from "@/lib/utils";

export default function PromptsListPage() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["prompts"],
    queryFn: () => request<PromptOut[]>("/prompts"),
  });

  const create = useMutation({
    mutationFn: () =>
      request<PromptOut>("/prompts", {
        method: "POST",
        data: {
          name: "Untitled prompt",
          description: "",
          body:
            "<role>\nYou are a helpful assistant.\n</role>\n\n<user>\n{{input}}\n</user>\n",
          variables: [{ name: "input", type: "string", required: true }],
          tags: [],
        },
      }),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["prompts"] });
      toast.success("Prompt created");
      window.location.href = `/studio/prompts/${p.id}`;
    },
    onError: () => toast.error("Could not create prompt"),
  });

  return (
    <div className="p-6 space-y-5 max-w-5xl">
      <header className="flex items-end justify-between gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Studio</div>
          <h1 className="text-2xl font-semibold tracking-tight">Prompts</h1>
          <p className="text-fg-muted mt-1 text-sm">
            Author reusable prompts with variables. Use <span className="kbd">{`{{var}}`}</span>{" "}
            placeholders.
          </p>
        </div>
        <Button onClick={() => create.mutate()} disabled={create.isPending}>
          <Plus className="h-4 w-4" /> New prompt
        </Button>
      </header>

      {q.isLoading && <div className="text-sm text-fg-muted">Loading…</div>}
      <div className="grid gap-3 md:grid-cols-2">
        {(q.data ?? []).map((p) => (
          <Card key={p.id}>
            <CardHeader className="flex flex-row items-start gap-3">
              <div className="min-w-0 flex-1">
                <CardTitle className="truncate">{p.name}</CardTitle>
                <CardDescription className="line-clamp-2 mt-1">
                  {p.description || <span className="italic text-fg-subtle">No description</span>}
                </CardDescription>
              </div>
              <Badge>v{p.version}</Badge>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {(p.tags ?? []).map((t) => (
                  <Badge key={t}>{t}</Badge>
                ))}
                <span className="text-xs text-fg-subtle ml-1">
                  Updated {formatRelative(p.updated_at)}
                </span>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link href={`/studio/prompts/${p.id}`}>
                  <Pencil className="h-3.5 w-3.5" /> Edit
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
        {(q.data ?? []).length === 0 && !q.isLoading && (
          <div className="surface col-span-full p-6 text-sm text-fg-muted">
            No prompts yet. Click <span className="kbd">New prompt</span> to start with a
            techniqued template.
          </div>
        )}
      </div>
    </div>
  );
}
