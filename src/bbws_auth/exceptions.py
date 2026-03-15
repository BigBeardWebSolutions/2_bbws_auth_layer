"""Exception hierarchy for bbws-auth authorization library."""

import json


class AuthError(Exception):
    """Base auth error with API Gateway-compatible response."""

    status_code: int = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def to_response(self) -> dict:
        """Convert to API Gateway proxy response format."""
        return {
            "statusCode": self.status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": self.message}),
        }


class UnauthorizedError(AuthError):
    """401 - missing or invalid credentials / claims."""

    status_code = 401


class ForbiddenError(AuthError):
    """403 - authenticated but insufficient permissions."""

    status_code = 403


class TenantMismatchError(AuthError):
    """403 - cross-tenant access attempt detected."""

    status_code = 403
