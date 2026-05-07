import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AgentsComingSoon() {
  return (
    <div className="p-6 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>OpenAI Agents SDK specs — coming in M3</CardTitle>
          <CardDescription>
            Build agent specs (instructions, tools, MCP refs) and export as Python or TypeScript
            snippets. The studio surfaces the deprecation date for the Assistants API
            (<span className="font-mono">2026-08-26</span>) and steers new agents toward the
            current Agents SDK + Responses API path.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-fg-muted">
          Latest guidance pulled from <span className="font-mono">developers.openai.com</span>.
        </CardContent>
      </Card>
    </div>
  );
}
