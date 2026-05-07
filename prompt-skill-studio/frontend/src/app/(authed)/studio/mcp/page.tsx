import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function McpComingSoon() {
  return (
    <div className="p-6 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>MCP server stubs — coming in M3</CardTitle>
          <CardDescription>
            Define tools, choose stdio / http / sse transport, and export a starter scaffold for
            either TypeScript (<span className="font-mono">@modelcontextprotocol/sdk</span>) or
            Python (<span className="font-mono">mcp</span>). The studio explicitly labels the
            output as a scaffold — you run the server locally.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-fg-muted">
          MCP is now native in OpenAI Agents SDK and the Responses API, and supported across
          Claude clients via the MCP Connector.
        </CardContent>
      </Card>
    </div>
  );
}
