import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

/**
 * NeevScore (300-900, from /api/meta) is the only score the interface shows. These checks read
 * the source and fail if the classic 0-100 score, or a copy of the scale, creeps back in.
 */

const GENERATED = ["api-schema.d.ts", "meta.fallback.ts"];
// The one place the classic score may appear: the line in the report's method section.
const CLASSIC_LINE = /classic|क्लासिक/i;

function sources(dir = "src"): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return sources(path);
    const code = /\.tsx?$/.test(entry.name) && !entry.name.endsWith(".test.ts");
    return code && !GENERATED.includes(entry.name) ? [path] : [];
  });
}

function withoutComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`])\/\/.*$/gm, "$1");
}

function offences(pattern: RegExp, allowed: (line: string, file: string) => boolean = () => false) {
  return sources().flatMap((file) =>
    withoutComments(readFileSync(file, "utf-8"))
      .split("\n")
      .filter((line) => pattern.test(line) && !allowed(line, file))
      .map((line) => `${file}: ${line.trim()}`),
  );
}

test("no 0-100 score copy is left", () => {
  const copy = /0[–-]100|\/ ?100\b|\b0 to 100\b|out of 100\b|starts at 100|100 में से|100 से शुरू/i;
  assert.deepEqual(
    offences(copy, (line) => CLASSIC_LINE.test(line)),
    [],
  );
});

test("the scale and the band edges are never written into the interface", () => {
  assert.deepEqual(offences(/\b(300|900|449|599|749|750)\b/), []);
});

test("no screen reads the classic score fields", () => {
  const classicField =
    /\.score\.(value|band|band_label|confidence|provisional|hard_stop|drivers|areas|checks_unread)\b/;
  const methodNote = (_line: string, file: string) => file.endsWith("MethodNote.tsx");
  assert.deepEqual(offences(classicField, methodNote), []);

  const summaryFields = /\b(check|summary|recent|latest|card)\.(score|band)\b|\b(old|new)_score\b/;
  assert.deepEqual(offences(summaryFields), []);
});

test("the old per-version band maps and score drawings are gone", () => {
  assert.deepEqual(offences(/t\.report\.bands|t\.credit\.bands|ScoreRing|V2_TONE|CreditDial/), []);
});
