import assert from "node:assert/strict";
import { test } from "node:test";

import { find as hi } from "./i18n/hi/find.ts";
import { find as en } from "./i18n/en/find.ts";

// A search can miss a project, so the card that appears when nothing was found states only that no
// record was found. It must never call the project illegal, unregistered or a fraud.
const BANNED = [
  /illegal/i,
  /fraud/i,
  /scam/i,
  /unregistered/i,
  /not registered/i,
  /फर्जी/,
  /धोखा/,
  /अवैध/,
  /गैरकानूनी/,
  /अपंजीकृत/,
];

function words(card: typeof en.notFound): string {
  return [card.title, card.note, card.stepsTitle, ...card.steps, card.reportTitle, card.reportLink, card.tryTitle, ...card.tryItems, card.tryButton].join(" ");
}

test("the not-found card never accuses the project", () => {
  for (const card of [en.notFound, hi.notFound]) {
    for (const word of BANNED) assert.doesNotMatch(words(card), word);
  }
});

test("the not-found card says only that no record was found, and what to do", () => {
  assert.equal(en.notFound.title, "We couldn't find a RERA registration for this project in public records.");
  assert.match(en.notFound.steps.join(" "), /in writing/);
  assert.match(en.notFound.steps.join(" "), /500 square metres/);
  assert.match(en.notFound.steps.join(" "), /Section 3/);
  assert.equal(hi.notFound.steps.length, en.notFound.steps.length);
});

test("the other cards do not accuse the project either", () => {
  const copy = [en.orderLead.body("Y"), en.builderResults.noneBody("Z"), hi.orderLead.body("Y")].join(" ");
  for (const word of BANNED) assert.doesNotMatch(copy, word);
});

test("the outside-Uttar-Pradesh answer is calm and names no other state", () => {
  assert.equal(
    en.outsideUp,
    "NeevCheck covers Uttar Pradesh RERA projects for now. Check this project on its own state's RERA website.",
  );
  for (const text of [en.outsideUp, hi.outsideUp]) {
    for (const word of BANNED) assert.doesNotMatch(text, word);
  }
});
