"""NeevScore v2 of a finished check, from its stored findings and source runs.

The orchestrator uses it when a check ends, and the store uses it to re-score checks made
before v2 existed. One path for both means an old report and a new one are scored identically.
"""

from app.models import Finding, SourceName, SourceRun
from app.scoring.v2.engine import score_v2
from app.scoring.v2.models import ScoreV2
from app.scoring.v2.pillars_read import partly_read, pillars_read

COMPLAINT_KINDS = ("promoter_complaints", "project_complaints")
UNAVAILABLE_LABELS: dict[SourceName, str] = {
    "registry": "Company registry",
    "insolvency": "Insolvency records",
    "land": "Land authority lists",
    "consumer": "Consumer cases (e-Jagriti)",
    "news": "News",
    "group": "Group companies",
    "sarfaesi": "Lender auction notices",
}


def score_from_runs(findings: list[Finding], runs: list[SourceRun]) -> ScoreV2:
    # A run that did not finish stores no checks_read, so this is what was really read.
    read = {check for run in runs for check in run.checks_read}
    # Checks stored before the complaint counts were a key check still hold those findings.
    if any(f.source == "uprera" and f.kind in COMPLAINT_KINDS for f in findings):
        read.add("rera_complaints")
    completed = [run.source for run in runs if run.status == "completed"]
    unavailable = [
        UNAVAILABLE_LABELS[run.source] + (f" ({run.message})" if run.message else "")
        for run in runs
        if run.status != "completed" and run.source in UNAVAILABLE_LABELS
    ]
    return score_v2(
        findings, pillars_read(read, completed), unavailable, partly_read(read, completed)
    )
