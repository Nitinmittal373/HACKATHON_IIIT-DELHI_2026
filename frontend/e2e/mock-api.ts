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

import type { components } from "../src/lib/api-schema";

// Everything this mock builds itself is typed from the generated contract, so a change to the
// backend's models breaks the compile here instead of silently serving a stale shape.
type Schemas = components["schemas"];

const FIXTURES = resolve(dirname(fileURLToPath(import.meta.url)), "fixtures");
const PORT = Number(process.env.MOCK_API_PORT ?? 8010);
const EVENT_DELAY_MS = Number(process.env.MOCK_EVENT_DELAY_MS ?? 40);
const ALLOWED_ORIGIN = process.env.MOCK_ALLOWED_ORIGIN ?? "http://localhost:3010";
// The second search result stands in for a visitor over the rate limit.
const RATE_LIMITED_RERA_ID = "UPRERAPRJ4878";

const read = (name: string): string => readFileSync(resolve(FIXTURES, name), "utf-8");
const json = (name: string): Record<string, unknown> => JSON.parse(read(name));

// A copy of the report with two tree nodes marked, so the flagged styling can be tested.
const FLAGGED_ID = "f".repeat(32);

let finished = false;
// A real replay with too few record types read to give a band; served under its own id.
const UNRATED_ID = "a1".repeat(16);
// A number of another state's RERA: NeevCheck answers calmly that it covers Uttar Pradesh only.
const OTHER_STATE_NUMBER = "P51800000937";

function send(res: ServerResponse, status: number, body: unknown, headers: Record<string, string> = {}) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Expose-Headers": "Retry-After",
    ...headers,
  });
  res.end(JSON.stringify(body));
}

async function streamEvents(res: ServerResponse, file = "events.sse") {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  });
  for (const block of read(file).trim().split("\n\n")) {
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

const recordedReport = (): Schemas["Report"] => json("report.json") as unknown as Schemas["Report"];

// The recorded report with what the credit-protection work added: a re-check that opens later,
// a pillar read only through UP-RERA's complaint counts, a company status from a secondary
// source, and e-Jagriti left for the buyer because of its CAPTCHA.
const CREDIT_ID = "c".repeat(32);
function creditReport(): Schemas["Report"] {
  const report = recordedReport();
  const [template] = report.findings;
  if (!template) throw new Error("the recorded report has no findings");
  const secondary: Schemas["Finding"] = {
    ...template,
    id: "secondary-company-status",
    source: "registry",
    kind: "company_status",
    title: "Company status: Active",
    verdict: "ok",
    reliability: "secondary",
  };
  const consumer: Schemas["SourceRun"] = {
    source: "consumer",
    status: "blocked",
    live_url: null,
    message: "Not checked automatically: the site needs a CAPTCHA",
    checks_read: [],
    manual_url: "https://e-jagriti.gov.in/advance-case-search",
  };
  const sources = [...report.check.sources.filter((run) => run.source !== "consumer"), consumer];
  const pillars = report.score_v2.pillars.map((pillar) =>
    pillar.id === "P2" ? { ...pillar, partly_read: "UP-RERA complaints" } : pillar,
  );
  const unread = report.score_v2.pillars_unread.filter((id) => id !== "P2");
  return {
    ...report,
    check: { ...report.check, id: CREDIT_ID, next_recheck_at: "2026-11-01T04:00:00Z", sources },
    findings: [secondary, ...report.findings],
    score_v2: { ...report.score_v2, pillars, pillars_unread: unread },
  };
}

/** The recorded check as "My reports" lists it (GET /api/checks?ids=). */
function recordedSummary(): Schemas["CheckSummary"] {
  const { check, project, score, display_score } = recordedReport();
  return {
    id: check.id,
    rera_id: check.rera_id,
    details_url: check.details_url,
    project: project.name,
    promoter: project.promoter,
    status: "completed",
    score: score.value,
    band: score.band,
    confidence: score.confidence,
    display_score,
    created_at: check.started_at,
    completed_at: check.completed_at,
  };
}

/** The recorded check with the facts the home page card shows (GET /api/checks?ids=). */
function recordedRecent(): Schemas["RecentCheck"] {
  const { check, project, score, score_v2 } = recordedReport();
  return {
    ...recordedSummary(),
    registered_on: project.registered_on,
    sources_read: check.sources.filter((run) => run.status === "completed").length,
    drivers: score.drivers.slice(0, 3),
    reasons: score_v2.reason_codes.filter((reason) => reason.code !== "R12").slice(0, 3),
  };
}

createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
  const path = url.pathname;

  if (req.method === "OPTIONS") {
    // The browser asks before any JSON POST made from another origin.
    res.writeHead(204, {
      "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    });
    return res.end();
  }

  if (path === "/api/health") return send(res, 200, { status: "ok" });

  if (path === "/api/projects/search") {
    const query = url.searchParams.get("q") ?? "";
    if (/nothing/i.test(query) || query === OTHER_STATE_NUMBER) {
      const none: Schemas["SearchResponse"] = {
        query,
        candidates: [],
        outside_up: query === OTHER_STATE_NUMBER,
        order_leads: [],
      };
      return send(res, 200, none);
    }
    return send(res, 200, { ...json("search.json"), query });
  }

  if (path === "/api/meta") return send(res, 200, json("meta.json"));

  if (path === "/api/limits") {
    const signedIn = Boolean(req.headers.authorization);
    const limits: Schemas["Limits"] = {
      // Like a deployment run for development; the sign-in rules have their own tests.
      require_signin: false,
      invite_only: false,
      checks_per_account_per_day: 2,
      reuse_report_days: 7,
      recheck_min_days: 7,
      live_checks_open: true,
      checks_left_today: signedIn ? 2 : null,
      invited: signedIn ? true : null,
    };
    return send(res, 200, limits);
  }

  if (path === "/api/featured") {
    // One saved check of a well-known project, as the gallery shows it.
    const { check, project, display_score } = recordedReport();
    const card: Schemas["FeaturedProject"] = {
      rera_id: project.rera_id,
      check_id: check.id,
      name: project.name,
      promoter: project.promoter,
      display_score,
      read_at: check.completed_at ?? check.started_at,
    };
    return send(res, 200, [card]);
  }

  if (path === "/api/sentinel/watches") {
    if (!req.headers.authorization) return send(res, 401, { detail: "Sign in to use this" });
    return send(res, 200, []);
  }

  if (path === "/api/sentinel/alerts") {
    // Alerts belong to the signed-in account; the real API answers 401 without its token.
    if (!req.headers.authorization) return send(res, 401, { detail: "Sign in to use this" });
    return send(res, 200, JSON.parse(read("alerts.json")));
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

  if (path === "/api/checks" && req.method === "GET") {
    const ids = (url.searchParams.get("ids") ?? "").split(",");
    const avenue = json("summary-6742.json") as unknown as Schemas["CheckSummary"];
    const known: Schemas["RecentCheck"][] = [
      recordedRecent(),
      { ...avenue, registered_on: null, sources_read: 0, drivers: [], reasons: [] },
    ];
    return send(res, 200, ids.flatMap((id) => known.filter((check) => check.id === id)));
  }

  if (path === "/api/checks/compare") {
    // The recorded comparison of the 8334 check with the 6742 page, in the order asked.
    const ids = (url.searchParams.get("ids") ?? "").split(",");
    const comparison = json("compare.json") as { projects: { check_id: string }[] };
    const projects = ids.flatMap((id) => comparison.projects.filter((p) => p.check_id === id));
    if (projects.length < 2) return send(res, 404, { detail: "No check with this id" });
    return send(res, 200, { ...comparison, projects });
  }

  if (path === "/api/promoters/projects") return send(res, 200, json("track-record.json"));

  const check = path.match(/^\/api\/checks\/([0-9a-f]{32})(\/events|\/report)?$/);
  if (check) {
    const [, id, tail] = check;
    if (id === UNRATED_ID && tail === "/report") return send(res, 200, json("report-unrated.json"));
    const known = json("check-created.json").id;
    if (id === FLAGGED_ID && tail === "/report") return send(res, 200, json("report-flagged.json"));
    if (id === CREDIT_ID && tail === "/report") return send(res, 200, creditReport());
    if (id !== known) return send(res, 404, { detail: "No check with this id" });
    if (tail === "/events") return streamEvents(res);
    if (tail === "/report") return send(res, 200, json("report.json"));
    return send(res, 200, finished ? json("check-done.json") : { ...json("check-created.json"), status: "running" });
  }

  return send(res, 404, { detail: "Not found" });
}).listen(PORT, () => console.log(`mock API on http://localhost:${PORT}`));
