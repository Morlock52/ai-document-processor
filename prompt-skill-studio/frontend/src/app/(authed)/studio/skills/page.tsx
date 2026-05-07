import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SkillsComingSoon() {
  return (
    <div className="p-6 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>Anthropic Skills authoring — coming in M2</CardTitle>
          <CardDescription>
            Author <span className="font-mono">SKILL.md</span> with frontmatter validation
            (name, description, allowed-tools, paths, disable-model-invocation, user-invocable,
            context, agent, effort, arguments) and ZIP export of <span className="font-mono">SKILL.md</span>
            {" + "}references and scripts.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-fg-muted">
          Tracking the latest format from{" "}
          <a className="text-brand hover:underline" href="https://code.claude.com/docs/en/skills">
            code.claude.com/docs/en/skills
          </a>
          .
        </CardContent>
      </Card>
    </div>
  );
}
