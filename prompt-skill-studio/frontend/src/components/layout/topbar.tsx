"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { request } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface Stale {
  vendor: "anthropic" | "openai";
  stale_since: string | null;
}

export function Topbar() {
  const [stale, setStale] = useState<Stale[]>([]);

  useEffect(() => {
    let alive = true;
    request<Stale[]>("/catalog/stale")
      .then((d) => alive && setStale(d.filter((s) => s.stale_since)))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  return (
    <header className="h-12 border-b border-border bg-bg-subtle flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        {stale.length > 0 && (
          <Link
            href="/diff"
            className="flex items-center gap-2 text-xs text-warning hover:underline"
            title="Some vendor docs failed to refresh on the last poll"
          >
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>
              Stale: {stale.map((s) => s.vendor).join(", ")}
            </span>
          </Link>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Badge tone="brand">Anthropic</Badge>
        <Badge tone="success">OpenAI</Badge>
        <span className="kbd ml-2">⌘K</span>
      </div>
    </header>
  );
}
