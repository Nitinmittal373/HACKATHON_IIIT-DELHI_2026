import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import find_check, get_store
from app.api.reports import assemble_report
from app.compare import Comparison, compare
from app.store import Store

# Included before the checks router, whose /api/checks/{check_id} would reject "compare".
router = APIRouter(tags=["checks"])

CHECK_ID = re.compile(r"^[0-9a-f]{32}$")
MIN_COMPARED, MAX_COMPARED = 2, 3


@router.get(
    "/api/checks/compare",
    responses={
        404: {"description": "One of the checks does not exist"},
        409: {"description": "One of the checks has no report"},
        422: {"description": "Not two or three valid ids"},
    },
)
def compare_checks(
    ids: Annotated[str, Query(max_length=120, description="Two or three check ids")],
    store: Annotated[Store, Depends(get_store)],
) -> Comparison:
    wanted = list(dict.fromkeys(part.strip() for part in ids.split(",") if part.strip()))
    if not MIN_COMPARED <= len(wanted) <= MAX_COMPARED or not all(map(CHECK_ID.match, wanted)):
        raise HTTPException(status_code=422, detail="Compare needs two or three different checks")
    reports = []
    for check_id in wanted:
        report = assemble_report(store, find_check(store, check_id))
        if report is None:
            raise HTTPException(
                status_code=409, detail=f"Check {check_id} has not finished with a score"
            )
        reports.append(report)
    return compare(reports)
