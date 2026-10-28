/**
 * The API's shapes, named for the app. Each one is an alias of a type generated from the
 * backend's OpenAPI contract (api-schema.d.ts), so nothing here is written by hand: change a
 * backend model, run `make contract`, and the compiler shows what the frontend must follow.
 */
import type { components } from "@/lib/api-schema";

type Schemas = components["schemas"];

export type Project = Schemas["Project"];
export type SearchResponse = Schemas["SearchResponse"];
export type OrderLead = Schemas["OrderLead"];
/** A builder's projects and company pages (GET /api/promoters/search). */
export type PromoterSearchResponse = Schemas["PromoterSearchResponse"];
export type CompanyHit = Schemas["CompanyHit"];
/** The numbers found in a PDF or in the text of a QR code (POST /api/extract). */
export type ExtractResponse = Schemas["ExtractResponse"];
export type CandidateStatus = NonNullable<Schemas["Project"]["status"]>;
export type SourceRun = Schemas["SourceRun"];
export type Check = Schemas["Check"];
export type Finding = Schemas["Finding"];

export type SourceName = SourceRun["source"];
export type RunStatus = SourceRun["status"];
export type CheckKey = SourceRun["checks_read"][number];
export type CheckStatus = Check["status"];
export type Reliability = Finding["reliability"];
export type Verdict = Finding["verdict"];
export type Area = Schemas["Driver"]["area"];

/** The classic 0-100 score. Screens show NeevScore (DisplayScore); this is kept for transparency. */
export type Score = Schemas["Score"];
export type Band = Score["band"];
export type Driver = Schemas["Driver"];
export type AreaScore = Schemas["AreaScore"];

/** NeevScore v2 (300-900), with its pillars and reason codes. */
export type ScoreV2 = Schemas["ScoreV2"];
export type BandV2 = ScoreV2["band"];
export type PillarId = Schemas["Pillar"]["id"];
export type Pillar = Schemas["Pillar"];
export type DriverV2 = Schemas["DriverV2"];
export type ReasonCode = Schemas["ReasonCode"];

/** The score every screen shows: value, band and how much was read. */
export type DisplayScore = Schemas["DisplayScore"];

/** GET /api/limits: what a live check costs a visitor, and the account's checks left today. */
export type Limits = Schemas["Limits"];
/** A saved check of a well-known project, for the gallery (GET /api/featured). */
export type FeaturedProject = Schemas["FeaturedProject"];

/** GET /api/meta: the score scale, band edges and pillar weights. */
export type Meta = Schemas["Meta"];

export type FamilyTree = Schemas["FamilyTree"];
export type FamilyProject = Schemas["FamilyProject"];
export type FamilyCompany = Schemas["FamilyCompany"];
export type FamilyFlag = NonNullable<FamilyCompany["flag"]>;
export type FamilyProjectState = FamilyProject["state"];

export type Report = Schemas["Report"];

/** What the app sends: one body type per POST route. */
export type CheckCreate = Schemas["CheckCreate"];
export type WatchCreate = Schemas["WatchCreate"];
export type CorrectionCreate = Schemas["CorrectionCreate"];

export type Watch = Schemas["Watch"];
export type Alert = Schemas["Alert"];
export type AlertChange = Schemas["FindingChange"];

/** One line of "My reports" (GET /api/checks?ids=). */
export type CheckSummary = Schemas["CheckSummary"];
/** A finished check shown on the home page (GET /api/checks/recent). */
export type RecentCheck = Schemas["RecentCheck"];

export type AreaPoints = Schemas["AreaPoints"];
export type PillarPoints = Schemas["PillarPoints"];
export type FindingLine = Schemas["FindingLine"];
/** One column of a comparison. null means the check could not read it, never "clean". */
export type ComparedProject = Schemas["ComparedProject"];
export type Comparison = Schemas["Comparison"];
export type InsolvencyStatus = NonNullable<ComparedProject["insolvency"]>;

/** A promoter's other UP-RERA projects, from Search on up-rera.in (GET /api/promoters/projects). */
export type TrackRecord = Schemas["TrackRecord"];
export type TrackedProject = Schemas["TrackedProject"];

/** One Server-Sent Event of a check; `type` says which payload `data` holds. */
export type CheckEvent =
  | Schemas["SourceStartedEvent"]
  | Schemas["SourceLiveUrlEvent"]
  | Schemas["SourceProgressEvent"]
  | Schemas["FindingAddedEvent"]
  | Schemas["SourceBlockedEvent"]
  | Schemas["SourceCompletedEvent"]
  | Schemas["CheckCompletedEvent"];
export type EventType = CheckEvent["type"];
export type CheckCompleted = Schemas["CheckCompletedData"];
/** The classic summary sent with check.completed, kept for older clients. */
export type ScoreSummary = Schemas["ScoreSummary"];
