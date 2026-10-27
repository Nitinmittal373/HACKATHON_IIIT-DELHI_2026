import assert from "node:assert/strict";
import { test } from "node:test";

import { safeNext } from "./safeNext.ts";

test("a path on this site is kept, with its query", () => {
  assert.equal(safeNext("/report/abc?watch=1"), "/report/abc?watch=1");
  assert.equal(safeNext("/reports"), "/reports");
});

test("anything that could leave the site goes home", () => {
  for (const bad of [
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "/\t/evil.example",
    "javascript:alert(1)",
    "evil.example",
    "",
    null,
    undefined,
  ]) {
    assert.equal(safeNext(bad), "/", String(bad));
  }
});
