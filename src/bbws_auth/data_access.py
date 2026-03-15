"""Tenant-scoped DynamoDB query helpers enforcing tenant isolation."""

from .exceptions import ForbiddenError
from .models import TenantContext


def query_tenant_data(table, tenant_ctx: TenantContext, sk_condition) -> dict:
    """Query DynamoDB with enforced tenant isolation.

    Forces PK to TENANT#{jwt_tenant_id} - the caller cannot
    override this to query another tenant's data.

    Args:
        table: boto3 DynamoDB Table resource
        tenant_ctx: Resolved TenantContext from PermissionResolver
        sk_condition: boto3 Key condition for the sort key

    Returns:
        DynamoDB query response dict

    Raises:
        ForbiddenError: If called by a platform user (must use
            query_tenant_data_as_platform instead)
    """
    if tenant_ctx.user_type == "platform":
        raise ForbiddenError(
            "Platform users must use query_tenant_data_as_platform"
        )

    from boto3.dynamodb.conditions import Key

    return table.query(
        KeyConditionExpression=(
            Key("pk").eq(f"TENANT#{tenant_ctx.tenant_id}") & sk_condition
        )
    )


def query_tenant_data_as_platform(
    table,
    tenant_ctx: TenantContext,
    target_tenant_id: str,
    sk_condition,
) -> dict:
    """Query another tenant's data - platform users only.

    Args:
        table: boto3 DynamoDB Table resource
        tenant_ctx: Resolved TenantContext (must be platform user)
        target_tenant_id: The tenant whose data to query
        sk_condition: boto3 Key condition for the sort key

    Raises:
        ForbiddenError: If caller is not a platform user or
            lacks "tenant:read" permission
    """
    if tenant_ctx.user_type != "platform":
        raise ForbiddenError("Only platform users can query other tenants")

    tenant_ctx.require_permission("tenant:read")

    from boto3.dynamodb.conditions import Key

    return table.query(
        KeyConditionExpression=(
            Key("pk").eq(f"TENANT#{target_tenant_id}") & sk_condition
        )
    )
