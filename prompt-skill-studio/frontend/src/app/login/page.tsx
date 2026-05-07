"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { request } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}

function LoginInner() {
  const router = useRouter();
  const search = useSearchParams();
  const next = search.get("next") || "/";
  const [passcode, setPasscode] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await request("/auth/login", { method: "POST", data: { passcode } });
      router.replace(next);
      router.refresh();
    } catch (err) {
      toast.error("Invalid passcode");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="w-full max-w-sm surface p-6">
        <div className="mb-5">
          <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Studio</div>
          <h1 className="text-xl font-semibold text-fg">Prompt &amp; Skill</h1>
          <p className="text-sm text-fg-muted mt-1">Enter the shared passcode to continue.</p>
        </div>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <Input
            type="password"
            placeholder="Passcode"
            value={passcode}
            onChange={(e) => setPasscode(e.target.value)}
            autoFocus
          />
          <Button type="submit" disabled={busy || !passcode}>
            {busy ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
