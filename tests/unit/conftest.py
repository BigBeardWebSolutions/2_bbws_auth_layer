"""Shared test fixtures for bbws-auth unit tests."""

import pytest


def make_v2_event(claims: dict) -> dict:
    """Create an HTTP API v2 event with the given JWT claims."""
    return {
        "version": "2.0",
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": claims,
                }
            }
        },
    }


def make_v1_event(claims: dict) -> dict:
    """Create a REST API v1 event with the given JWT claims."""
    return {
        "requestContext": {
            "authorizer": {
                "claims": claims,
            }
        },
    }


@pytest.fixture
def platform_claims():
    """JWT claims for a platform super-admin user."""
    return {
        "sub": "platform-user-sub-001",
        "email": "admin@bigbeard.co.za",
        "custom:user_type": "platform",
        "custom:tenant_id": "",
        "cognito:groups": "[platform-super-admin, platform-admin]",
    }


@pytest.fixture
def tenant_claims():
    """JWT claims for a tenant editor user."""
    return {
        "sub": "tenant-user-sub-001",
        "email": "user@example.com",
        "custom:user_type": "tenant",
        "custom:tenant_id": "tenant-abc-123",
        "cognito:groups": "",
    }


@pytest.fixture
def v2_platform_event(platform_claims):
    """HTTP API v2 event for a platform user."""
    return make_v2_event(platform_claims)


@pytest.fixture
def v1_platform_event(platform_claims):
    """REST API v1 event for a platform user."""
    return make_v1_event(platform_claims)


@pytest.fixture
def v2_tenant_event(tenant_claims):
    """HTTP API v2 event for a tenant user."""
    return make_v2_event(tenant_claims)
