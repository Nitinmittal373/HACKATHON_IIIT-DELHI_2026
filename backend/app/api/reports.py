from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CheckId, find_check, get_store
from app.models import Check, Report
from app.store import Store

router = APIRouter(tags=["checks"])


@router.get("/api/checks/{check_id}/report", responses={409: {"description": "No report yet"}})
def get_report(check_id: CheckId, store: Annotated[Store, Depends(get_store)]) -> Report:
    check = find_check(store, check_id)
    if check.status in ("queued", "running"):
        raise HTTPException(status_code=409, detail="The check is still running")
    report = assemble_report(store, check)
    if report is None:
        raise HTTPException(status_code=409, detail="The check failed, so there is no report")
    return report


def assemble_report(store: Store, check: Check) -> Report | None:
    """The report of a finished check, or None when it failed and has no score."""
    score = store.get_score(check.id)
    project = store.get_project(check.rera_id)
    if check.status != "completed" or score is None or project is None:
        return None
    findings = store.list_findings(check.id)
    points = {driver.finding_id: driver.points for driver in score.drivers}
    findings.sort(key=lambda f: points.get(f.id, 0))
    timeline = sorted((f for f in findings if f.occurred_on), key=lambda f: f.occurred_on)
    return Report(
        check=check,
        project=project,
        score=score,
        findings=findings,
        timeline=timeline,
        score_v2=store.get_score_v2(check.id),
    )
