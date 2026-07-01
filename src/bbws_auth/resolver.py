"""PermissionResolver - main entry point for bbws-auth authorization."""

import boto3

from .claims import extract_claims
from .exceptions import ForbiddenError, UnauthorizedError
from .models import EffectivePermissions, TenantContext, UserType
from .platform_permissions import (
    PLATFORM_PERMISSION_MAP,
    highest_platform_role,
)


class PermissionResolver:
    """Resolves effective permissions for any user on any portal.

    Instantiate OUTSIDE the Lambda handler to reuse the DynamoDB connection
    across invocations within the same execution environment.

    Usage:
        resolver = PermissionResolver(table_name="tenants")

        def handler(event, context):
            ctx = resolver.resolve(event)
            ctx.require_permission("site:deploy")
            ...
    """

    def __init__(self, table_name: str = "tenants"):
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def resolve(self, event: dict) -> TenantContext:
        """Resolve effective permissions from an API Gateway event.

        Args:
            event: API Gateway event (HTTP API v2 or REST API v1)

        Returns:
            TenantContext: Immutable context with identity and permissions

        Raises:
            UnauthorizedError: Missing or invalid JWT claims
            ForbiddenError: No role assignment or insufficient permissions
        """
        claims = extract_claims(event)

        user_type_str = claims.get("custom:user_type", "")
        if not user_type_str:
            raise UnauthorizedError("Missing custom:user_type in JWT")

        try:
            user_type = UserType(user_type_str)
        except ValueError:
            raise UnauthorizedError(f"Unknown user_type: {user_type_str}")

        if user_type == UserType.PLATFORM:
            return self._resolve_platform(claims)
        else:
            return self._resolve_tenant(claims)

    def _resolve_platform(self, claims: dict) -> TenantContext:
        """Resolve permissions for a platform (BBWS staff) user."""
        groups = claims.get("cognito:groups", [])
        role = highest_platform_role(groups)

        if role is None:
            raise ForbiddenError("Platform user has no recognized Cognito groups")

        permissions = PLATFORM_PERMISSION_MAP[role]

        return TenantContext(
            user_sub=claims.get("sub", ""),
            email=claims.get("email", ""),
            user_type=UserType.PLATFORM.value,
            tenant_id=None,
            role=role,
            effective_permissions=permissions,
        )

    def _resolve_tenant(self, claims: dict) -> TenantContext:
        """Resolve permissions for a tenant (customer) user."""
        tenant_id = (
            claims.get("tenant_id")
            or claims.get("custom:tenant_id")
            or claims.get("custom:tid", "")
        )
        user_sub = claims.get("sub", "")

        if not tenant_id:
            raise UnauthorizedError("Tenant user missing tenant_id claim")

        # Query 1: Get user role assignment
        user_response = self._table.get_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": f"USER#{user_sub}"}
        )
        user_record = user_response.get("Item")
        if not user_record:
            raise ForbiddenError(
                f"No role assignment found for user {user_sub} in tenant {tenant_id}"
            )

        role_name = user_record.get("role", "")
        overrides = user_record.get("permission_overrides", {})
        granted = set(overrides.get("grant", []))
        revoked = set(overrides.get("revoke", []))

        # Query 2: Get role definition
        role_response = self._table.get_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": f"ROLE#{role_name}"}
        )
        role_record = role_response.get("Item")
        if not role_record:
            raise ForbiddenError(
                f"Role '{role_name}' not found for tenant {tenant_id}"
            )

        base_permissions = set(role_record.get("permissions", []))

        # effective = (base ∪ granted) − revoked
        effective = (base_permissions | granted) - revoked

        return TenantContext(
            user_sub=user_sub,
            email=claims.get("email", ""),
            user_type=UserType.TENANT.value,
            tenant_id=tenant_id,
            role=role_name,
            effective_permissions=frozenset(effective),
        )
