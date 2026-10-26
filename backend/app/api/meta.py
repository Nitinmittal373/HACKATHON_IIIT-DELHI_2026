from fastapi import APIRouter

from app.meta import Meta, build_meta

router = APIRouter(tags=["meta"])


@router.get("/api/meta")
def get_meta() -> Meta:
    """The score scale, band edges and pillar weights, so no client hard-codes them."""
    return build_meta()
