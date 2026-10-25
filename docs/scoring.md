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

## Rules that keep the score honest

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

## Confidence

Confidence is the share of seven key checks that were actually read: registration, completion date, extensions, company status, insolvency, land dues and consumer cases. A blocked, failed or unreadable source leaves its checks unread. "Extensions" counts as read when the project's summary page was read, because that page lists the extensions granted (or none). "Insolvency" counts as read only when a page actually reported the case; finding no page proves nothing. "Land dues" counts as read only when every land authority list for the project's district was read. If UP-RERA itself cannot be read, the check fails and no score is shown.

## Bands

| Band | Range |
| --- | --- |
| Low | 80–100 |
| Moderate | 60–79 |
| High | 40–59 |
| Critical | 0–39 |
| Not enough evidence yet (`insufficient_evidence`) | any score, when confidence is below 50% and there is no hard stop |

A hard stop is always Critical, however little else was read: one verified serious record is enough.

## Worked example

Supertech Eco Village-I Phase I-C (`UPRERAPRJ8334`), checked live on 25 Oct 2026. Every source was read except the land authority lists. The same numbers are a test in `backend/tests/test_recorded_check.py`, replayed from the recording.

| Finding | Area | Penalty | Points |
| --- | --- | --: | --: |
| Completion date on record (30 Dec 2017) passed 105 months ago; project still listed as Ongoing | Project execution (20%) | 70 | −14 |
| 2,803 complaints on UP-RERA against the promoter | Builder history (15%) | 60 | −9 |
| 15 complaints on UP-RERA about this project | Legal and courts (15%) | 40 | −6 |
| Three news stories on delays (10 each, secondary) | News (10%) | 30 | −3 |
| **NeevScore** | | | **68 · Moderate** |

Shown with no points: registration (ok), company status (Active), the insolvency admission of 25 Mar 2022, a news report that the insolvency covers the whole company (**unverified**: no court order was read, so it cannot cap the score), one consumer case on e-Jagriti, and the Supreme Court's NBCC order (context).

Confidence is 86% (6 of 7 checks): land dues were not read because the authorities' lists could not be fetched. If a CAPTCHA had stopped e-Jagriti, confidence would be 71% and the score would stay 68.
