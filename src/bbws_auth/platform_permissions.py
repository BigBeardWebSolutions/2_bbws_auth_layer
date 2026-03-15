"""Hardcoded platform permission map for BBWS staff roles."""

from __future__ import annotations

PLATFORM_PERMISSION_MAP: dict[str, frozenset] = {
    "platform-super-admin": frozenset([
        "tenant:create", "tenant:read", "tenant:edit", "tenant:delete", "tenant:settings",
        "user:invite", "user:remove", "user:list", "user:manage",
        "billing:read", "billing:edit",
        "monitoring:read", "monitoring:configure",
        "platform:configure", "platform:deploy",
        "audit:read",
    ]),
    "platform-admin": frozenset([
        "tenant:create", "tenant:read", "tenant:edit", "tenant:settings",
        "user:invite", "user:remove", "user:list", "user:manage",
        "billing:read", "billing:edit",
        "monitoring:read",
        "audit:read",
    ]),
    "platform-operator": frozenset([
        "tenant:read",
        "user:list",
        "billing:read",
        "monitoring:read",
        "audit:read",
    ]),
    "platform-viewer": frozenset([
        "tenant:read",
        "monitoring:read",
        "audit:read",
    ]),
}

PLATFORM_ROLE_PRECEDENCE: list[str] = [
    "platform-super-admin",
    "platform-admin",
    "platform-operator",
    "platform-viewer",
]


def highest_platform_role(groups: list[str]) -> str | None:
    """Return the highest-precedence platform role from a list of Cognito groups.

    Returns None if no recognized platform roles are found.
    """
    for role in PLATFORM_ROLE_PRECEDENCE:
        if role in groups:
            return role
    return None
