import type { BandKey } from "@/components/ScoreRing";

/** Colour of a small status dot: a risk signal, except "brand" which marks NeevCheck itself. */
export type Tone = "ok" | "warn" | "bad" | "brand";

export interface ExampleDriver {
  label: string;
  /** Share of the bar to fill, 0 to 100. */
  fill: number;
  points: number;
  tone: Tone;
}

export interface ExampleFinding {
  tone: Tone;
  bold: string;
  text: string;
}

/** One line of "what the records say", with where it came from. */
export interface RecordFact {
  tone: Tone;
  title: string;
  meta: string;
}

/** What the UP-RERA project page showed, for the illustration of a live check. */
export interface RegisterPage {
  registeredOn: string;
  completionDue: string;
  projectType: string;
  extensions: string;
  registeredLabel: string;
  dueLabel: string;
  extensionsLabel: string;
}

export interface ExampleReport {
  /** A short name for places with little room. */
  shortName: string;
  /** The day the live check was read. */
  readOn: string;
  name: string;
  reraId: string;
  promoter: string;
  score: number;
  band: BandKey;
  bandLabel: string;
  confidencePercent: number;
  drivers: ExampleDriver[];
  findings: ExampleFinding[];
  facts: RecordFact[];
  register: RegisterPage;
}
