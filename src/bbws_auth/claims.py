"""JWT claim extraction from API Gateway events (HTTP API v2 + REST API v1)."""

from __future__ import annotations

from .exceptions import UnauthorizedError


def extract_claims(event: dict) -> dict:
    """Extract JWT claims from API Gateway event.

    Handles both:
    - HTTP API v2: event.requestContext.authorizer.jwt.claims
    - REST API v1: event.requestContext.authorizer.claims

    Returns:
        dict: Normalized claims with cognito:groups parsed to list.

    Raises:
        UnauthorizedError: If no claims are found in the event.
    """
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})

    if event.get("version") == "2.0":
        claims = authorizer.get("jwt", {}).get("claims", {})
    else:
        claims = authorizer.get("claims", {})

    if not claims:
        raise UnauthorizedError("No JWT claims found in event")

    # Normalize cognito:groups to list
    claims["cognito:groups"] = _parse_cognito_groups(
        claims.get("cognito:groups", "")
    )

    return claims


def _parse_cognito_groups(groups_value) -> list[str]:
    """Parse cognito:groups from JWT claims.

    Handles:
    - Bracket-wrapped string: "[admin, user]"  (HTTP API v2)
    - Comma-separated string: "admin,user"     (REST API v1)
    - Single string: "admin"                   (single group)
    - List: ["admin", "user"]                  (already parsed)
    - Empty/None: ""                           (no groups)
    """
    if not groups_value:
        return []
    if isinstance(groups_value, list):
        return groups_value
    s = str(groups_value).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [g.strip() for g in s.split(",") if g.strip()]
