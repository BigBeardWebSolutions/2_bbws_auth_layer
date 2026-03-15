"""Tests for exception hierarchy."""

import json

from bbws_auth.exceptions import (
    AuthError,
    ForbiddenError,
    TenantMismatchError,
    UnauthorizedError,
)


class TestExceptions:
    def test_unauthorized_status_code(self):
        err = UnauthorizedError("test")
        assert err.status_code == 401

    def test_forbidden_status_code(self):
        err = ForbiddenError("test")
        assert err.status_code == 403

    def test_tenant_mismatch_status_code(self):
        err = TenantMismatchError("test")
        assert err.status_code == 403

    def test_inheritance(self):
        assert issubclass(UnauthorizedError, AuthError)
        assert issubclass(ForbiddenError, AuthError)
        assert issubclass(TenantMismatchError, AuthError)
        assert issubclass(AuthError, Exception)

    def test_to_response_format(self):
        err = ForbiddenError("Permission denied")
        resp = err.to_response()
        assert resp["statusCode"] == 403
        assert resp["headers"]["Content-Type"] == "application/json"
        body = json.loads(resp["body"])
        assert body["error"] == "Permission denied"

    def test_message_preserved(self):
        err = UnauthorizedError("No JWT claims found in event")
        assert str(err) == "No JWT claims found in event"
        assert err.message == "No JWT claims found in event"
