"""Who is calling: the signed-in account behind a bridge token, and the limit on account routes."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from app.api.deps import client_ip, get_clock, get_settings
from app.bridge_token import BridgeUser, InvalidToken, verify_bridge_token
from app.config import Settings
from app.ratelimit import RateLimiter


def get_account_limiter(request: Request) -> RateLimiter:
    return request.app.state.account_limiter


def rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[RateLimiter, Depends(get_account_limiter)],
) -> None:
    wait = limiter.retry_after(client_ip(request, settings))
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests from this address, please wait a minute",
            headers={"Retry-After": str(wait)},
        )


def current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    authorization: Annotated[str | None, Header()] = None,
) -> BridgeUser:
    if settings.auth_bridge_secret is None:
        raise HTTPException(status_code=503, detail="Accounts are not set up on this server")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in to use this")
    try:
        return verify_bridge_token(token, settings.auth_bridge_secret.get_secret_value(), clock())
    except InvalidToken:
        message = "Your sign-in expired; please sign in again"
        raise HTTPException(status_code=401, detail=message) from None


User = Annotated[BridgeUser, Depends(current_user)]
