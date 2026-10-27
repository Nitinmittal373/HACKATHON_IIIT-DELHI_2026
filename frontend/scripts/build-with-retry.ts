/**
 * `next build` for the browser tests, tried up to three times.
 *
 * The build downloads the Google fonts, and that request sometimes fails or returns an
 * unreadable answer on a busy CI runner. Nothing in the app is wrong when it does, so one
 * retry is cheaper than a red run.
 *
 *   node scripts/build-with-retry.ts
 */
import { spawnSync } from "node:child_process";

const ATTEMPTS = 3;
const PAUSE_MS = 5_000;

for (let attempt = 1; attempt <= ATTEMPTS; attempt++) {
  const { status } = spawnSync("npx", ["next", "build"], { stdio: "inherit", shell: true });
  if (status === 0) process.exit(0);
  if (attempt === ATTEMPTS) {
    console.error(`next build failed ${ATTEMPTS} times in a row; giving up.`);
    process.exit(status ?? 1);
  }
  console.error(`next build failed (attempt ${attempt} of ${ATTEMPTS}); trying again in ${PAUSE_MS / 1000}s.`);
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, PAUSE_MS);
}
