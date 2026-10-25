# NeevScore method

NeevScore is a number from 0 to 100. It is **deterministic**: the same records always produce the same score, and every point lost is linked to the record that caused it. The code is in [`backend/app/scoring/`](../backend/app/scoring/); keep it and this page in sync.

## Formula

```text
NeevScore = round(100 − Σ (weight × penalty))
```

- Each **area** has a weight (they add up to 100%).
- Each **finding** has a penalty from 0 to 100 within its area.
- Penalties within one area are capped at 100 (News at 60). The cap is spent on the largest penalties first, so the drivers shown in a report add up to the score exactly.
- A **hard stop** caps the final score at 39 (Critical).

## Weights

| Area | Weight |
| --- | --: |
| UP-RERA compliance | 25% |
| Project execution | 20% |
| Legal and courts | 15% |
| Financial and insolvency | 15% |
| Builder history | 15% |
| News | 10% |

Land authority dues count under **Financial and insolvency**.

## Penalties

Penalties come only from parsed facts, never from rules written for one builder.

| Finding | Area | Penalty |
| --- | --- | --: |
| Completion date extended *n* times (COVID-19 force-majeure extensions not counted) | Project execution | 30 + 20 × (*n* − 1) |
| Completion date on record passed more than 12 months ago, project still listed as Ongoing | Project execution | 40 |
| Completion date on record passed more than 24 months ago, project still listed as Ongoing | Project execution | 70 |
| Insolvency limited to another project | Financial and insolvency | 60 |
| Insolvency of the company or this project | Financial and insolvency | 100 and hard stop |
| Listed for unpaid land authority dues | Financial and insolvency | 70 |
| UP-RERA registration lapsed or revoked | UP-RERA compliance | 100 and hard stop |
| One news story on delays (secondary) | News | 10 each |
| Complaints on UP-RERA against the promoter, all projects: at least 20 / 100 / 500 | Builder history | 20 / 40 / 60 |
| Complaints on UP-RERA about this project: at least 1 / 10 | Legal and courts | 15 / 40 |

The completion date on record is the latest date UP-RERA shows for the project. Until extension orders are read (Phase 2), the delay rule is applied to that date. Complaint counts come from the project's UP-RERA summary page, and each finding links to it.

Everything else in a report (registration date, a completion date not yet passed, an insolvency admission whose scope is decided by a later order, court orders such as the Supreme Court's NBCC ruling) is shown as evidence with 0 points.

## Rules that keep the score honest

| Rule | Why |
| --- | --- |
| Absence of a record never adds points | "Nothing found" may only mean a site was unreadable |
| An unreadable source lowers confidence, not the score | We never punish a project for a CAPTCHA |
| Insolvency counts fully only when it covers the company or this project | Supertech's process was limited to Eco Village-II by NCLAT |
| An admission and the order that sets its scope are two findings; only the scope is scored | The same case is never counted twice |
| A petition that is not yet admitted is a "review" finding | Filing is not the same as admission |
| News is a secondary source | It can only add small penalties and is marked for review |
| COVID-19 force-majeure extensions are not counted as delays | They were granted to all projects |
| Delay is measured from the latest approved end date, not the original one | Extensions already count once; the delay must not count them again |
| A completion or occupancy certificate on record skips the delay penalty | The certificate is shown as a "review" finding: verify possession before relying on it |
| A "Proforma of Completion Certificate" is not a certificate | It is the blank template every project uploads at registration; it never skips the delay penalty and is not shown |

## Confidence

Confidence is the share of seven key checks that were actually read: registration, completion date, extensions, company status, insolvency, land dues and consumer cases. A blocked, failed or not-yet-connected source leaves its checks unread. If UP-RERA itself cannot be read, the check fails and no score is shown.

## Bands

| Band | Range |
| --- | --- |
| Low | 80–100 |
| Moderate | 60–79 |
| High | 40–59 |
| Critical | 0–39 |

## Worked example

Supertech Eco Village-I Phase I-C (`UPRERAPRJ8334`) with every source read, as recorded on 24 Oct 2026. The same numbers are a test in `backend/tests/test_scoring.py`.

| Finding | Area | Penalty | Points |
| --- | --- | --: | --: |
| Completion date extended 3 times | Project execution (20%) | 70 | −14 |
| Insolvency limited to another project | Financial and insolvency (15%) | 60 | −9 |
| One news story on delays | News (10%) | 10 | −1 |
| **NeevScore** | | | **76 · Moderate** |

Confidence is 71% (5 of 7 checks) because consumer cases (e-Jagriti, CAPTCHA) and the completion date could not be read.

Until the Phase 2 agents land, a live check reads UP-RERA only. On 25 Oct 2026 that gave:

| Finding | Area | Penalty | Points |
| --- | --- | --: | --: |
| Completion date on record (30 Dec 2017) passed 105 months ago; project still listed as Ongoing | Project execution (20%) | 70 | −14 |
| 2,803 complaints on UP-RERA against the promoter | Builder history (15%) | 60 | −9 |
| 15 complaints on UP-RERA about this project | Legal and courts (15%) | 40 | −6 |
| **NeevScore** | | | **71 · Moderate** |

Confidence is 29% (registration and completion date, 2 of 7 checks): most of the record is still unread.
