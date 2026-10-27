import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { test } from "node:test";

import { BRIDGE_TOKEN_SECONDS, mintBridgeToken } from "./bridgeToken.ts";

const NOW = Date.UTC(2026, 9, 27, 12, 0, 0);

test("the token is HS256, names the Google account and lasts ten minutes", () => {
  const token = mintBridgeToken({ sub: "google-1", email: "a@example.com" }, "secret", NOW);
  const [head, body, signature] = token.split(".");
  assert.deepEqual(JSON.parse(Buffer.from(head!, "base64url").toString()), { alg: "HS256", typ: "JWT" });
  const claims = JSON.parse(Buffer.from(body!, "base64url").toString());
  assert.equal(claims.sub, "google-1");
  assert.equal(claims.email, "a@example.com");
  assert.equal(claims.exp - claims.iat, BRIDGE_TOKEN_SECONDS);
  assert.equal(claims.exp, NOW / 1000 + 600);
  assert.equal(signature, createHmac("sha256", "secret").update(`${head}.${body}`).digest("base64url"));
});

test("a different secret gives a different signature", () => {
  const user = { sub: "google-1", email: "a@example.com" };
  assert.notEqual(mintBridgeToken(user, "one", NOW), mintBridgeToken(user, "two", NOW));
});
