"""The short-lived token the web app sends to prove who is signed in.

Google signs a visitor in on the Next.js site (Auth.js). The site then mints an HS256 token,
valid for ten minutes, with the Google account id as `sub` and the e-mail, signed with a secret
only the site and this API know (AUTH_BRIDGE_SECRET). The API never talks to Google: it only
checks that signature, which keeps one login system and no extra dependency.
"""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime


class InvalidToken(ValueError):
    """The token is missing, malformed, badly signed or expired."""


@dataclass(frozen=True)
class BridgeUser:
    sub: str
    email: str


def verify_bridge_token(token: str, secret: str, now: datetime) -> BridgeUser:
    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidToken("not a token")
    head, body, signature = parts
    expected = hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_unb64(signature), expected):
        raise InvalidToken("bad signature")
    if _json(head).get("alg") != "HS256":
        raise InvalidToken("unsupported algorithm")
    claims = _json(body)
    expires = claims.get("exp")
    if not isinstance(expires, int | float) or expires <= now.timestamp():
        raise InvalidToken("expired")
    sub, email = claims.get("sub"), claims.get("email")
    if not isinstance(sub, str) or not sub or not isinstance(email, str):
        raise InvalidToken("missing account")
    return BridgeUser(sub=sub, email=email)


def _unb64(text: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except ValueError:
        raise InvalidToken("not base64") from None


def _json(text: str) -> dict[str, object]:
    try:
        value = json.loads(_unb64(text))
    except ValueError:
        raise InvalidToken("not json") from None
    if not isinstance(value, dict):
        raise InvalidToken("not an object")
    return value
