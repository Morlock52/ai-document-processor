"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { request } from "@/lib/api";
import type { KeyOut, Vendor } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatRelative } from "@/lib/utils";

export default function KeysPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["keys"], queryFn: () => request<KeyOut[]>("/keys") });

  const [vendor, setVendor] = useState<Vendor>("anthropic");
  const [label, setLabel] = useState("");
  const [apiKey, setApiKey] = useState("");

  const create = useMutation({
    mutationFn: () =>
      request<KeyOut>("/keys", {
        method: "POST",
        data: { vendor, label, api_key: apiKey },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["keys"] });
      setLabel("");
      setApiKey("");
      toast.success("Key saved (encrypted at rest)");
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? "Could not save key";
      toast.error(typeof msg === "string" ? msg : "Could not save key");
    },
  });

  const del = useMutation({
    mutationFn: (id: string) => request(`/keys/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["keys"] });
      toast.success("Key removed");
    },
  });

  return (
    <div className="p-6 space-y-5 max-w-3xl">
      <header>
        <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Settings</div>
        <h1 className="text-2xl font-semibold tracking-tight">Vendor API keys</h1>
        <p className="text-fg-muted mt-1 text-sm">
          Keys are encrypted with AES-256-GCM using <span className="font-mono">STUDIO_MASTER_KEY</span>{" "}
          and decrypted only in-process during a run. They are never logged.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Add a key</CardTitle>
          <CardDescription>One key per vendor is enough; add more if you want labels.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-[140px_1fr_1fr_auto] items-start">
          <select
            value={vendor}
            onChange={(e) => setVendor(e.target.value as Vendor)}
            className="h-9 rounded-md border border-border bg-bg-subtle text-sm px-2"
          >
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
          </select>
          <Input
            placeholder="Label (e.g. personal)"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <Input
            type="password"
            placeholder="sk-... or sk-ant-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <Button
            disabled={!label || !apiKey || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? "Saving…" : "Save"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Stored keys</CardTitle>
        </CardHeader>
        <CardContent>
          {q.isLoading && <div className="text-sm text-fg-muted">Loading…</div>}
          <ul className="divide-y divide-border -mx-2">
            {(q.data ?? []).map((k) => (
              <li key={k.id} className="px-2 py-3 flex items-center gap-3">
                <Badge tone={k.vendor === "anthropic" ? "brand" : "success"}>{k.vendor}</Badge>
                <div className="min-w-0">
                  <div className="text-sm">{k.label}</div>
                  <div className="text-xs font-mono text-fg-muted">
                    {k.fingerprint} · added {formatRelative(k.created_at)}
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-auto"
                  onClick={() => del.mutate(k.id)}
                  disabled={del.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </li>
            ))}
            {(q.data ?? []).length === 0 && !q.isLoading && (
              <li className="px-2 py-3 text-sm text-fg-muted">No keys yet.</li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
