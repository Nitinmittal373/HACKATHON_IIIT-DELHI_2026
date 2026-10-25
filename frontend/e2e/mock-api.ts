/**
 * A stand-in for the NeevCheck backend that replays recorded answers (e2e/fixtures/, written by
 * backend/scripts/export_e2e_fixtures.py). Some pages (report, live check) fetch the API from
 * the Next server, where a browser tool cannot intercept requests, so the browser tests start
 * this small server instead of the real backend. Nothing here reaches the network.
 *
 *   node e2e/mock-api.ts          (port MOCK_API_PORT, default 8010)
 */
import { readFileSync } from "node:fs";
import { createServer, type ServerResponse } from "node:http";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FIXTURES = resolve(dirname(fileURLToPath(import.meta.url)), "fixtures");
const PORT = Number(process.env.MOCK_API_PORT ?? 8010);
const EVENT_DELAY_MS = Number(process.env.MOCK_EVENT_DELAY_MS ?? 40);
const ALLOWED_ORIGIN = process.env.MOCK_ALLOWED_ORIGIN ?? "http://localhost:3010";
// The second search result stands in for a visitor over the rate limit.
const RATE_LIMITED_RERA_ID = "UPRERAPRJ4878";

const read = (name: string): string => readFileSync(resolve(FIXTURES, name), "utf-8");
const json = (name: string): Record<string, unknown> => JSON.parse(read(name));

let finished = false;

function send(res: ServerResponse, status: number, body: unknown, headers: Record<string, string> = {}) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Expose-Headers": "Retry-After",
    ...headers,
  });
  res.end(JSON.stringify(body));
}

async function streamEvents(res: ServerResponse) {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  });
  for (const block of read("events.sse").trim().split("\n\n")) {
    res.write(`${block}\n\n`);
    await new Promise((done) => setTimeout(done, EVENT_DELAY_MS));
  }
  finished = true;
  res.end();
}

function readBody(req: import("node:http").IncomingMessage): Promise<string> {
  return new Promise((done) => {
    let text = "";
    req.on("data", (chunk) => (text += chunk));
    req.on("end", () => done(text));
  });
}

createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
  const path = url.pathname;

  if (path === "/api/health") return send(res, 200, { status: "ok" });

  if (path === "/api/projects/search") {
    const query = url.searchParams.get("q") ?? "";
    if (/nothing/i.test(query)) return send(res, 200, { query, candidates: [] });
    return send(res, 200, { ...json("search.json"), query });
  }

  if (path === "/api/checks" && req.method === "POST") {
    const body = JSON.parse(await readBody(req)) as { rera_id?: string };
    if (body.rera_id === RATE_LIMITED_RERA_ID) {
      const detail = "Too many checks from this address, please wait a minute";
      return send(res, 429, { detail }, { "Retry-After": "30" });
    }
    finished = false;
    return send(res, 202, json("check-created.json"));
  }

  const check = path.match(/^\/api\/checks\/([0-9a-f]{32})(\/events|\/report)?$/);
  if (check) {
    const [, id, tail] = check;
    const known = json("check-created.json").id;
    if (id !== known) return send(res, 404, { detail: "No check with this id" });
    if (tail === "/events") return streamEvents(res);
    if (tail === "/report") return send(res, 200, json("report.json"));
    return send(res, 200, finished ? json("check-done.json") : { ...json("check-created.json"), status: "running" });
  }

  return send(res, 404, { detail: "Not found" });
}).listen(PORT, () => console.log(`mock API on http://localhost:${PORT}`));
