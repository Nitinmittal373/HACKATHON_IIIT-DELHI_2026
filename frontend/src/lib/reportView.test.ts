import assert from "node:assert/strict";
import test from "node:test";

import { builderFromListings } from "./reportView.ts";

test("the builder is flagged as identified from listings only when that finding exists", () => {
  assert.equal(builderFromListings([{ kind: "registration" }, { kind: "builder_identity" }]), true);
  assert.equal(builderFromListings([{ kind: "registration" }]), false);
});
