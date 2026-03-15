"""Permission enforcement decorators for Lambda handlers."""

import functools

from .exceptions import AuthError
from .resolver import PermissionResolver


def require_permission(*permissions: str, table_name: str = "tenant_permissions"):
    """Decorator that enforces permission checks on a Lambda handler.

    Usage:
        @require_permission("site:deploy")
        def handler(event, context, tenant_ctx=None):
            # tenant_ctx is injected by the decorator
            ...

        @require_permission("site:create", "site:edit")
        def handler(event, context, tenant_ctx=None):
            # user must have ALL listed permissions
            ...

    Args:
        *permissions: One or more permission strings (all required)
        table_name: DynamoDB table name for tenant permissions
    """
    resolver = PermissionResolver(table_name=table_name)

    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(event, context):
            try:
                tenant_ctx = resolver.resolve(event)
                for perm in permissions:
                    tenant_ctx.require_permission(perm)
                return handler_func(event, context, tenant_ctx=tenant_ctx)
            except AuthError as e:
                return e.to_response()

        return wrapper

    return decorator
