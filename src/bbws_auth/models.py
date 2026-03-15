"""Immutable data models for bbws-auth authorization library."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .exceptions import ForbiddenError


class UserType(str, Enum):
    """User type determined by custom:user_type JWT claim."""

    PLATFORM = "platform"
    TENANT = "tenant"


@dataclass(frozen=True)
class EffectivePermissions:
    """Resolved permission set for a user."""

    role: str
    base_permissions: frozenset
    granted_overrides: frozenset
    revoked_overrides: frozenset
    effective: frozenset


@dataclass(frozen=True)
class TenantContext:
    """Immutable context carrying user identity and permissions through a request."""

    user_sub: str
    email: str
    user_type: str
    tenant_id: str | None
    role: str
    effective_permissions: frozenset

    def has_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        return permission in self.effective_permissions

    def require_permission(self, permission: str) -> None:
        """Require a specific permission, raising ForbiddenError if denied."""
        if permission not in self.effective_permissions:
            raise ForbiddenError(
                f"Permission '{permission}' denied for role '{self.role}'"
            )

    def require_any_permission(self, *permissions: str) -> None:
        """Require at least one of the given permissions."""
        if not any(p in self.effective_permissions for p in permissions):
            raise ForbiddenError(
                f"None of {list(permissions)} granted for role '{self.role}'"
            )
