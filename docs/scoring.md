# NeevScore method

NeevScore is a number from 300 to 900, like a credit score: higher is safer. It is **the score** shown on every screen. It is **deterministic**: the same records always produce the same score, and every point lost is linked to the record that caused it. The code is in [`backend/app/scoring/v2/`](../backend/app/scoring/v2/); keep it and this page in sync. The first version of the score (0–100) is described at the end of this page and is kept for transparency only.

## Where it is served

The backend owns the scale. Every response that shows a score carries a `display_score` (`value`, `band`, `hard_stop`, `confidence`, `provisional`): the report, the check and its events, My reports, the recent checks, compare, Sentinel alerts and a promoter's other projects. The full detail (pillars, reason codes, drivers) is the report's `score_v2`. `GET /api/meta` returns the scale (300 and 900), the band edges, the pillar weights and the reason codes, so the frontend never keeps its own copy.

Every stored check is scored again with the current rules once when the API starts (idempotent: the same findings give the same score), so an old report and `GET /api/checks/recent` read exactly as a new check would. A check made before NeevScore existed is scored from its stored findings and source runs the same way.

## Formula

```text
NeevScore v2 = clip(900 − 6 × Σ (weight × pillar penalty), 300, 900)
```

Each pillar penalty is 0–100 and capped (news at 60). The cap is spent on the largest penalties first, so the drivers and reason codes add up to the score. A **hard stop** forces the High band (value at most 449) and says why.

## Why it follows CRISIL's split

Credit ratings weigh business, financial, project and management risk separately instead of one blended number. v2 does the same with six pillars, so a buyer sees *which kind* of risk lowers the score. The weights are **transparent expert priors, to be calibrated on labelled stalled-project lists**; they are not fitted statistics.

## Pillars and penalties

| Pillar | Weight | Penalties |
| --- | --: | --- |
| P1 Regulatory compliance (RERA) | 30% | Registration lapsed or revoked 100 (**hard stop**); extended: 30 + 20 per extra; revised date more than 12 / 24 months after the promised one: 40 / 70; completion date passed and the project not completed (`past_end_date`): the same 40 / 70 steps by months overdue, and when both lateness findings are present only the larger counts; QPRs missed in the last 4 quarters: 15 each (max 60); penalty orders: 20 each |
| P2 Delivery track record | 20% | Share of the group's RERA projects delayed over 12 months (0–100); any group project lapsed: 40; UP-RERA complaints against the promoter across all its projects: 1 each (max 40) |
| P3 Legal and insolvency | 25% | Promoter in CIRP 100 (**hard stop**, official NCLT/IBBI/MCA page only); sister company or other project in insolvency 50; RERA complaints about the project 10 each (max 100); pending cases 5 each (max 40) |
| P4 Financial and corporate health | 15% | Company or director struck off or disqualified 40; recent charge 20; late MCA filings 20; SARFAESI auction notice 60 |
| P5 Land authority and approvals | 5% | On a land authority defaulter list 70; failed package deposit 50; no OC/CC past due 30 |
| P6 Sentiment and news | 5% | Delay or protest article known to be from the last 12 months: 10 each (max 60). An undated article is shown but not scored. Secondary, shown for review |

## Bands

| Band | Range |
| --- | --- |
| Low risk | 750–900 |
| Watch | 600–749 |
| Elevated risk | 450–599 |
| High risk | 300–449 |

## Confidence

The share of the six pillars with at least one source read. A band is shown only when the UP-RERA record (P1) was read **and** at least 4 of the 6 pillars were read. Otherwise the band is "Not enough evidence yet": the number is kept as a provisional value, never shown as a score. A hard stop from an official page always shows. Compare ranks only checks that have a band.

## Reason codes

The report shows the four codes that cost the most points, like a credit report. Each links to its findings and sources.

| Code | Meaning |
| --- | --- |
| R01 | Registration lapsed or revoked |
| R02 | Completion extended N times |
| R03 | Revised completion date N months after the promised one |
| R04 | QPRs missed (n of the last 4) |
| R05 | RERA complaints or penalty orders |
| R06 | Promoter or sister company in insolvency |
| R07 | Director linked to struck-off, disqualified or insolvent companies |
| R08 | Land authority dues or approvals default |
| R09 | Charges or SARFAESI action on assets |
| R10 | Pending litigation (n cases) |
| R11 | Adverse news or protests (n articles) |
| R12 | Data unavailable (source down or CAPTCHA). **Never adds a penalty**; it only lowers confidence |
| R13 | Builder record: complaints against the promoter across its UP-RERA projects ("Builder complaint record"), and other projects of the same group delayed or lapsed (added: P2 has no code in the first list) |
| R14 | Late filings with the company registry (added for the same reason) |

Findings that map to no v2 rule (a registration date, a court order, an unverified insolvency report) still appear in the evidence list with 0 v2 points. The v2 reason codes use only facts the code can read; a signal that cannot be read honestly stays unread and appears under R12.

## No number without evidence

When the band gate above is not met (band `insufficient_evidence`), `display_score.value` is `null` and every screen shows a dash with "Not enough evidence yet · n of 6 record types read". The computed figure is kept as `provisional_value` and appears only in the method section, labelled as provisional. Compare and "best on records" ignore such projects. A check that read only UP-RERA and one or two other sources therefore shows no score, however clean it looks: a missing record never adds points.

## Worked example

Supertech Eco Village-I Phase I-C (`UPRERAPRJ8334`), checked live with every source on. The same numbers are in the recorded fixture the browser tests replay.

| Pillar | Weight | Penalty | Points |
| --- | --: | --: | --: |
| P1 Regulatory compliance (RERA): completion date 105 months overdue | 30% | 70 | −126 |
| P2 Delivery track record: 5 of 5 group projects read are more than 12 months past their completion date (the 2,803 complaints against the promoter use the same pillar, whose cap is spent) | 20% | 100 | −120 |
| P3 Legal and insolvency: 15 complaints on UP-RERA about this project | 25% | 100 | −150 |
| P4 Financial and corporate health | 15% | 0 | 0 |
| P5 Land authority and approvals (not read) | 5% | 0 | 0 |
| P6 Sentiment and news: three recent stories on delays | 5% | 30 | −9 |
| **NeevScore** | | | **495 · Elevated** |

Five of six pillars were read (confidence 83%). Land authority lists could not be read and e-Jagriti stopped at its CAPTCHA, so they appear as reason code R12 and cost nothing.


# Classic score (0–100)

The first version of the score, computed from the same findings and returned as `score` next to `display_score`. It is **kept for transparency only**: the interface shows NeevScore (300–900) everywhere, and the classic number appears as one small line in the report's method section. It is deterministic like NeevScore, and its code is in [`backend/app/scoring/`](../backend/app/scoring/); keep it and this section in sync.

### Formula

```text
NeevScore = round(100 − Σ (weight × penalty))
```

- Each **area** has a weight (they add up to 100%).
- Each **finding** has a penalty from 0 to 100 within its area.
- Penalties within one area are capped at 100 (News at 60). The cap is spent on the largest penalties first, so the drivers shown in a report add up to the score exactly.
- A **hard stop** caps the final score at 39 (Critical).

### Weights

| Area | Weight |
| --- | --: |
| UP-RERA compliance | 25% |
| Project execution | 20% |
| Legal and courts | 15% |
| Financial and insolvency | 15% |
| Builder history | 15% |
| News | 10% |

Land authority dues count under **Financial and insolvency**.

### Penalties

Penalties come only from parsed facts, never from rules written for one builder.

| Finding | Area | Penalty |
| --- | --- | --: |
| Completion date extended *n* times (COVID-19 force-majeure extensions not counted) | Project execution | 30 + 20 × (*n* − 1) |
| Completion date on record passed more than 12 months ago, project not listed as completed | Project execution | 40 |
| Completion date on record passed more than 24 months ago, project not listed as completed | Project execution | 70 |
| Insolvency limited to another project | Financial and insolvency | 60 |
| Insolvency of the company or this project | Financial and insolvency | 100 and hard stop |
| Listed for unpaid land authority dues | Financial and insolvency | 50 |
| UP-RERA registration lapsed or revoked | UP-RERA compliance | 100 and hard stop |
| One news story on delays (secondary) | News | 10 each |
| Complaints on UP-RERA against the promoter, all projects: at least 20 / 100 / 500 | Builder history | 20 / 40 / 60 |
| Complaints on UP-RERA about this project: at least 1 / 10 | Legal and courts | 15 / 40 |

Any project whose UP-RERA type is not a completed one (Ongoing, New and so on) is late once that date has passed.

The completion date on record is the latest date UP-RERA shows for the project: the original or revised date, a permit's end date, or the end of the latest extension in the "Extension Granted" table on the project summary page. The delay rule is applied to that date. COVID-19 force-majeure rows in that table are not counted as extensions but do move the date.

UP-RERA keeps the type "Ongoing" after a project is finished. A project counts as completed when its summary page shows a completion certificate upload date (or the type reads exactly "Completed"). Complaint counts come from the project's UP-RERA summary page, and each finding links to it.

Everything else in a report (registration date, a completion date not yet passed, an insolvency admission whose scope is decided by a later order, court orders such as the Supreme Court's NBCC ruling) is shown as evidence with 0 points.

### Rules that keep the score honest

| Rule | Why |
| --- | --- |
| Absence of a record never adds points | "Nothing found" may only mean a site was unreadable |
| An unreadable source lowers confidence, not the score | We never punish a project for a CAPTCHA |
| Insolvency counts fully only when it covers the company or this project | Supertech's process was limited to Eco Village-II by NCLAT |
| A hard stop needs an official page | A news report that says an insolvency covers the company or this project is shown as "unverified" for review with 0 points; only an NCLT, NCLAT, IBBI or Supreme Court page can cap the score at Critical |
| A company whose registry status is under CIRP or liquidation is a hard stop | The promoter company itself is in insolvency. "Active" is shown as context and costs nothing |
| An admission and the order that sets its scope are two findings; only the scope is scored | The same case is never counted twice |
| A petition that is not yet admitted is a "review" finding | Filing is not the same as admission |
| News is a secondary source | It can only add small penalties and is marked for review |
| COVID-19 force-majeure extensions are not counted as delays | They were granted to all projects |
| Delay is measured from the latest approved end date, not the original one | Extensions already count once; the delay must not count them again |
| A completion or occupancy certificate on record skips the delay penalty | The certificate is shown as a "review" finding: verify possession before relying on it |
| A "Proforma of Completion Certificate" is not a certificate | It is the blank template every project uploads at registration; it never skips the delay penalty and is not shown |
| Too little evidence gives no band | Below 50% confidence the band is "Not enough evidence yet"; the score is still shown, marked provisional |

### Confidence

Confidence is the share of seven key checks that were actually read: registration, completion date, extensions, company status, insolvency, land dues and consumer cases. A blocked, failed or unreadable source leaves its checks unread. "Extensions" counts as read when the project's summary page was read, because that page lists the extensions granted (or none). "Insolvency" counts as read only when a page actually reported the case; finding no page proves nothing. "Land dues" counts as read only when every land authority list for the project's district was read. If UP-RERA itself cannot be read, the check fails and no score is shown.

### Bands

| Band | Range |
| --- | --- |
| Low | 80–100 |
| Moderate | 60–79 |
| High | 40–59 |
| Critical | 0–39 |
| Not enough evidence yet (`insufficient_evidence`) | any score, when confidence is below 50% and there is no hard stop |

A hard stop is always Critical, however little else was read: one verified serious record is enough.

### Worked example

Supertech Eco Village-I Phase I-C (`UPRERAPRJ8334`), checked live on 25 Oct 2026. Every source was read except the land authority lists. The same numbers are a test in `backend/tests/test_recorded_check.py`, replayed from the recording.

| Finding | Area | Penalty | Points |
| --- | --- | --: | --: |
| Completion date on record (30 Dec 2017) passed 105 months ago; project still listed as Ongoing | Project execution (20%) | 70 | −14 |
| 2,803 complaints on UP-RERA against the promoter | Builder history (15%) | 60 | −9 |
| 15 complaints on UP-RERA about this project | Legal and courts (15%) | 40 | −6 |
| Three news stories on delays (10 each, secondary) | News (10%) | 30 | −3 |
| **NeevScore** | | | **68 · Moderate** |

Shown with no points: registration (ok), company status (Active), the insolvency admission of 25 Mar 2022, a news report that the insolvency covers the whole company (**unverified**: no court order was read, so it cannot cap the score), and the Supreme Court's NBCC order (context).

Confidence is 71% (5 of 7 checks): land dues were not read because the authorities' lists could not be fetched, and e-Jagriti stopped at its CAPTCHA. Neither changes the score of 68.

