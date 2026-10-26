import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError

from app.api.deps import client_ip, get_settings, get_web
from app.config import Settings
from app.extract import (
    MAX_BYTES,
    MAX_TEXT,
    ExtractError,
    ExtractResponse,
    ExtractText,
    candidates_from_document,
    numbers_in_document,
    pdf_text,
)
from app.ratelimit import RateLimiter
from app.states.confirm import confirm_on_portals
from app.tinyfish import WebClient

router = APIRouter(tags=["projects"])

# Reading a PDF is CPU work; a hostile file must not hold a worker for long.
PDF_SECONDS = 20
TOO_BIG = "This file is larger than 5 MB"
NO_NUMBER = (
    "We could not find a RERA registration number in this file. Ask the builder for the "
    "number in writing, or search by the project's name."
)


def get_extract_limiter(request: Request) -> RateLimiter:
    return request.app.state.extract_limiter


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_extract_limiter)],
) -> None:
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many files from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


@router.post(
    "/api/extract",
    dependencies=[Depends(rate_limit)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"text": {"type": "string", "maxLength": MAX_TEXT}},
                        "required": ["text"],
                    }
                },
            },
        }
    },
    responses={
        413: {"description": "The file is larger than 5 MB"},
        415: {"description": "Only a PDF, or the text of a QR code, is accepted"},
        422: {"description": "The file could not be read"},
    },
)
async def extract_numbers(
    request: Request, web: Annotated[WebClient, Depends(get_web)]
) -> ExtractResponse:
    """RERA numbers in a PDF brochure or agreement, or in the text a QR code held.

    The file is read in memory and never stored. A photo is not accepted: the browser decodes
    its QR code and sends only the text.
    """
    kind = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if kind == "application/pdf":
        source, text = "your document", await read_pdf(request)
    elif kind == "application/json":
        source, text = "your QR code", await read_text(request)
    else:
        raise HTTPException(status_code=415, detail="Send a PDF, or the text of a QR code as JSON")
    numbers = numbers_in_document(text)
    if not numbers:
        return ExtractResponse(source=source, numbers=[], candidates=[], message=NO_NUMBER)
    candidates = candidates_from_document(numbers)
    # A portal that cannot be reached leaves the numbers shown, just unconfirmed.
    candidates = await confirm_on_portals(candidates, web)
    return ExtractResponse(source=source, numbers=numbers, candidates=candidates)


async def read_pdf(request: Request) -> str:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=TOO_BIG)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BYTES:
            raise HTTPException(status_code=413, detail=TOO_BIG)
    try:
        return await asyncio.wait_for(asyncio.to_thread(pdf_text, bytes(body)), PDF_SECONDS)
    except ExtractError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except TimeoutError:
        raise HTTPException(status_code=422, detail="This PDF took too long to read") from None


async def read_text(request: Request) -> str:
    try:
        return ExtractText.model_validate(json.loads(await request.body())).text[:MAX_TEXT]
    except (ValueError, ValidationError):
        raise HTTPException(status_code=422, detail='Send JSON like {"text": "..."}') from None
