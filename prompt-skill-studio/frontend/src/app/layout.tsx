import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "Prompt & Skill Studio",
  description:
    "Author and test prompts, Skills, agents, and MCP stubs for OpenAI and Anthropic. Stays current with vendor guidelines.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
