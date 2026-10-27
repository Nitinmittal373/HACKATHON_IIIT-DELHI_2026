import type { Page, Route } from "@playwright/test";

const API = "http://localhost:8010";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "GET, POST, DELETE",
};

export interface Person {
  id: string;
  name: string;
  email: string;
}

export const ASHA: Person = { id: "google-asha", name: "Asha Buyer", email: "asha@example.com" };
export const BALA: Person = { id: "google-bala", name: "Bala Buyer", email: "bala@example.com" };

/**
 * Stands in for Google, Auth.js and the account routes of the API, with one list of saved
 * reports and alerts per account, so a test can sign several people in and out of one browser.
 * Everything else (searching, running a check, a report) is still answered by the mock API.
 */
export class FakeAccounts {
  /** Saved check ids per account id, newest first. */
  readonly saved = new Map<string, string[]>();
  /** The alerts each account has; an account not listed has none. */
  readonly alerts = new Map<string, unknown[]>();
  /** Every POST /api/me/reports the page made. */
  readonly saves: { account: string; ids: string[] }[] = [];
  /** The Authorization header of every POST /api/checks, to see the token go along. */
  readonly checkTokens: (string | undefined)[] = [];
  private person: Person | null = null;

  /** The person Google would now have signed in; null is signed out. */
  signInAs(person: Person | null) {
    this.person = person;
  }

  async install(page: Page) {
    await page.route("**/api/auth/session", (route) =>
      route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(
          this.person
            ? { user: { ...this.person, image: null }, expires: "2999-01-01T00:00:00.000Z" }
            : {},
        ),
      }),
    );
    await page.route("**/api/bridge-token", (route) =>
      this.person
        ? route.fulfill({ contentType: "application/json", body: JSON.stringify({ token: `token-${this.person.id}` }) })
        : route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"Not signed in"}' }),
    );
    // Auth.js really answers the sign-out; here the fake Google forgets the person too.
    await page.route("**/api/auth/signout", (route) => {
      this.person = null;
      return route.continue();
    });

    await this.api(page, "/api/me/reports", async (route, account) => {
      const request = route.request();
      if (request.method() === "POST") {
        const ids = (request.postDataJSON() as { ids: string[] }).ids;
        this.saves.push({ account, ids });
        this.saved.set(account, [...ids, ...(this.saved.get(account) ?? []).filter((id) => !ids.includes(id))]);
      }
      return this.listOf(route, account, 50);
    });
    await this.api(page, "/api/me/recent", (route, account) => this.listOf(route, account, 6));
    await this.api(page, "/api/sentinel/alerts", (route, account) =>
      route.fulfill({
        contentType: "application/json",
        headers: CORS,
        body: JSON.stringify(this.alerts.get(account) ?? []),
      }),
    );
    await page.route(`${API}/api/checks`, async (route) => {
      const request = route.request();
      if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
      const token = request.headers().authorization;
      this.checkTokens.push(token);
      const answer = await route.fetch();
      const account = token?.replace("Bearer token-", "");
      if (account && answer.ok()) {
        const { id } = (await answer.json()) as { id: string };
        this.saved.set(account, [id, ...(this.saved.get(account) ?? []).filter((known) => known !== id)]);
      }
      return route.fulfill({ response: answer });
    });
  }

  /** An account route: 401 without a token, otherwise handled for the account the token names. */
  private async api(page: Page, path: string, handle: (route: Route, account: string) => Promise<void>) {
    await page.route(`${API}${path}`, (route) => {
      const request = route.request();
      if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS });
      const token = request.headers().authorization ?? "";
      if (!token.startsWith("Bearer token-")) {
        return route.fulfill({ status: 401, contentType: "application/json", headers: CORS, body: '{"detail":"Sign in"}' });
      }
      return handle(route, token.replace("Bearer token-", ""));
    });
  }

  /** The account's saved checks as the API lists them, read from the mock API. */
  private async listOf(route: Route, account: string, limit: number) {
    const ids = (this.saved.get(account) ?? []).slice(0, limit);
    const answer = await route.fetch({ url: `${API}/api/checks?ids=${ids.join(",")}`, method: "GET", headers: {} });
    return route.fulfill({ contentType: "application/json", headers: CORS, body: await answer.text() });
  }
}
