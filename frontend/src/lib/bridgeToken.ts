import { createHmac } from "node:crypto";

export const BRIDGE_TOKEN_SECONDS = 10 * 60;

function part(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

/**
 * The token the site hands the browser to prove who is signed in to the API: HS256, valid for
 * ten minutes, signed with a secret only the site and the API know. The API checks the same
 * signature (backend/app/bridge_token.py); it never talks to Google.
 */
export function mintBridgeToken(user: { sub: string; email: string }, secret: string, nowMs: number): string {
  const head = part({ alg: "HS256", typ: "JWT" });
  const issued = Math.floor(nowMs / 1000);
  const body = part({ sub: user.sub, email: user.email, iat: issued, exp: issued + BRIDGE_TOKEN_SECONDS });
  const signature = createHmac("sha256", secret).update(`${head}.${body}`).digest("base64url");
  return `${head}.${body}.${signature}`;
}
