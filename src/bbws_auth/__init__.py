"""bbws-auth: Shared authorization library for the Kimmy AI platform."""

from .claims import extract_claims
from .data_access import query_tenant_data, query_tenant_data_as_platform
from .decorators import require_permission
from .exceptions import (
    AuthError,
    ForbiddenError,
    TenantMismatchError,
    UnauthorizedError,
)
from .models import EffectivePermissions, TenantContext, UserType
from .resolver import PermissionResolver

__all__ = [
    "PermissionResolver",
    "TenantContext",
    "EffectivePermissions",
    "UserType",
    "extract_claims",
    "AuthError",
    "UnauthorizedError",
    "ForbiddenError",
    "TenantMismatchError",
    "query_tenant_data",
    "query_tenant_data_as_platform",
    "require_permission",
]
