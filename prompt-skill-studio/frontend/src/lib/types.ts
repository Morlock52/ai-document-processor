export type Vendor = "anthropic" | "openai";

export type CatalogKind = "model" | "feature" | "beta" | "technique" | "pricing";

export interface CatalogEntry {
  vendor: Vendor;
  kind: CatalogKind;
  slug: string;
  name: string;
  props: Record<string, unknown>;
  source_url: string;
  captured_at: string;
}

export interface ChangeEntry {
  vendor: Vendor;
  source_url: string;
  fetched_at: string;
  status_code: number;
  summary: string | null;
  diff: string | null;
}

export interface KeyOut {
  id: string;
  vendor: Vendor;
  label: string;
  fingerprint: string;
  created_at: string;
  last_used_at: string | null;
}

export interface PromptVariable {
  name: string;
  type: string;
  required: boolean;
  default?: unknown;
  description?: string;
}

export interface PromptOut {
  id: string;
  name: string;
  description: string;
  body: string;
  variables: PromptVariable[];
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
}
