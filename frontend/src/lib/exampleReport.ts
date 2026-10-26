/** Colour of a small status dot: a risk signal, except "brand" which marks NeevCheck itself. */
export type Tone = "ok" | "warn" | "bad" | "brand";

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
  /** The NeevScore of that check (display_score.value), shown only where the page says "example". */
  score: number;
  facts: RecordFact[];
  register: RegisterPage;
}
