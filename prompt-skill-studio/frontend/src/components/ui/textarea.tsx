"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "block w-full rounded-md border border-border bg-bg-subtle px-3 py-2 text-sm font-mono",
        "placeholder:text-fg-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60",
        "min-h-[120px] leading-relaxed",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";
