"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { request } from "@/lib/api";
import type { PromptOut } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PromptEditorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["prompt", params.id],
    queryFn: () => request<PromptOut>(`/prompts/${params.id}`),
  });

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [body, setBody] = useState("");
  const [tagsCsv, setTagsCsv] = useState("");

  useEffect(() => {
    if (q.data) {
      setName(q.data.name);
      setDescription(q.data.description ?? "");
      setBody(q.data.body ?? "");
      setTagsCsv((q.data.tags ?? []).join(", "));
    }
  }, [q.data]);

  const save = useMutation({
    mutationFn: () =>
      request<PromptOut>(`/prompts/${params.id}`, {
        method: "PATCH",
        data: {
          name,
          description,
          body,
          tags: tagsCsv
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["prompt", params.id] });
      qc.invalidateQueries({ queryKey: ["prompts"] });
      toast.success("Saved");
    },
    onError: () => toast.error("Save failed"),
  });

  const del = useMutation({
    mutationFn: () => request(`/prompts/${params.id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["prompts"] });
      toast.success("Deleted");
      router.replace("/studio/prompts");
    },
    onError: () => toast.error("Delete failed"),
  });

  const variables = (q.data?.variables ?? []).map((v) => v.name);

  return (
    <div className="p-6 space-y-5 max-w-6xl">
      <header className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Prompt</div>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="text-2xl font-semibold tracking-tight h-11 px-2 bg-transparent border-transparent hover:border-border focus-visible:border-border"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => del.mutate()} disabled={del.isPending}>
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            <Save className="h-4 w-4" />
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-[1fr_280px]">
        <Card>
          <CardHeader>
            <CardTitle>Body</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="Short description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="min-h-[420px]"
              spellCheck={false}
              placeholder={
                "Use XML-tag scaffolding for Claude:\n<role>\n  ...\n</role>\n\n<user>\n  {{input}}\n</user>"
              }
            />
            <Input
              placeholder="tags, comma, separated"
              value={tagsCsv}
              onChange={(e) => setTagsCsv(e.target.value)}
            />
          </CardContent>
        </Card>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Variables</CardTitle>
            </CardHeader>
            <CardContent>
              {variables.length === 0 ? (
                <div className="text-sm text-fg-muted">
                  Add <span className="kbd">{`{{name}}`}</span> placeholders in the body. M2 will
                  surface a typed editor here.
                </div>
              ) : (
                <ul className="flex flex-wrap gap-1">
                  {variables.map((v) => (
                    <li key={v}>
                      <Badge tone="brand">{v}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Technique tips</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-fg-muted space-y-2">
              <p>
                <span className="text-fg">Anthropic:</span> use XML tags for structure, prefill the
                assistant turn for stricter formats, prefer chain-of-thought via{" "}
                <span className="font-mono">&lt;thinking&gt;</span> scratchpads.
              </p>
              <p>
                <span className="text-fg">OpenAI:</span> place static system content first to
                maximise prompt-cache hits; pin to dated snapshots in production.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
