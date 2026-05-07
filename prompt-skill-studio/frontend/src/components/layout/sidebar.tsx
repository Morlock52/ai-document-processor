"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  GitCompare,
  KeyRound,
  LayoutDashboard,
  Library,
  PlugZap,
  ScrollText,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/catalog", label: "Catalog", icon: Library },
  { href: "/diff", label: "Changes", icon: GitCompare },
  { href: "/studio/prompts", label: "Prompts", icon: ScrollText },
  { href: "/studio/skills", label: "Skills", icon: BookOpen },
  { href: "/studio/agents", label: "Agents", icon: Wand2 },
  { href: "/studio/mcp", label: "MCP", icon: PlugZap },
  { href: "/settings/keys", label: "Keys", icon: KeyRound },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 shrink-0 border-r border-border bg-bg-subtle py-4 px-3 flex flex-col gap-1">
      <div className="px-2 pb-3 mb-2 border-b border-border">
        <div className="text-[11px] uppercase tracking-widest text-fg-subtle">Studio</div>
        <div className="text-base font-semibold leading-tight text-fg">Prompt &amp; Skill</div>
      </div>
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/" && pathname?.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-2 px-2.5 h-8 rounded-md text-sm transition-colors",
              active
                ? "bg-bg-muted text-fg"
                : "text-fg-muted hover:bg-bg-muted hover:text-fg"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
      <div className="mt-auto pt-3 px-2 text-[11px] text-fg-subtle">
        <div className="font-mono">v0.1.0 · M1</div>
      </div>
    </aside>
  );
}
