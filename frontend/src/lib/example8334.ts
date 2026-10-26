import type { ExampleReport } from "@/lib/exampleReport";

/**
 * The home page's examples all come from one real check of UPRERAPRJ8334, read live on
 * 25 Oct 2026, which gave NeevScore 621 (Watch). The same check is recorded in
 * backend/tests/fixtures/check_8334.json and its numbers are asserted in
 * backend/tests/test_recorded_check.py, so this file must follow it. The home page labels
 * every use of it as an example.
 */
export const EXAMPLE_REPORT: ExampleReport = {
  shortName: "Eco Village-I Ph I-C",
  readOn: "25 Oct 2026",
  name: "Supertech Eco Village-I Phase I-C",
  reraId: "UPRERAPRJ8334",
  promoter: "SUPERTECH LIMITED",
  score: 621,
  facts: [
    {
      tone: "bad",
      title: "Completion date passed 105 months ago",
      meta: "UP-RERA · due 30 Dec 2017, still Ongoing",
    },
    {
      tone: "ok",
      title: "Registered on UP-RERA",
      meta: "UPRERAPRJ8334 · 09 Aug 2017",
    },
    {
      tone: "warn",
      title: "Builder admitted to insolvency in 2022",
      meta: "NCLT 25 Mar 2022 · scope not confirmed by an order",
    },
  ],
  register: {
    registeredOn: "09-08-2017",
    completionDue: "30-12-2017",
    projectType: "Ongoing",
    extensions: "None on record",
    registeredLabel: "Registered 09 Aug 2017",
    dueLabel: "Due 30 Dec 2017",
    extensionsLabel: "No extension on record",
  },
};
