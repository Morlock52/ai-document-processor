import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { URL } from "node:url";

const PORT = process.env.PORT || 3000;
const MODEL = "gpt-4o-realtime-preview";

async function handleRequest(req, res) {
  const { pathname } = new URL(req.url, `http://${req.headers.host}`);
  if (pathname === "/") {
    const html = await readFile(new URL("./index.html", import.meta.url));
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(html);
    return;
  }
  if (pathname === "/session") {
    const response = await fetch(
      "https://api.openai.com/v1/realtime/sessions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ model: MODEL, voice: "verse" }),
      },
    );
    const data = await response.json();
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(data));
    return;
  }
  res.writeHead(404);
  res.end("Not found");
}

createServer(handleRequest).listen(PORT, () => {
  console.log(`Realtime demo at http://localhost:${PORT}`);
});
