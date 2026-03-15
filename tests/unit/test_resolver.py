"""Tests for PermissionResolver."""

from unittest.mock import MagicMock, patch

import pytest

from bbws_auth.exceptions import ForbiddenError, UnauthorizedError
from bbws_auth.resolver import PermissionResolver

from .conftest import make_v2_event


class TestResolverPlatform:
    """Test platform user resolution (no DynamoDB)."""

    @patch("bbws_auth.resolver.boto3")
    def test_resolves_platform_super_admin(self, mock_boto3):
        resolver = PermissionResolver(table_name="tenant_permissions")
        event = make_v2_event({
            "sub": "admin-sub",
            "email": "admin@bbws.co.za",
            "custom:user_type": "platform",
            "cognito:groups": "[platform-super-admin]",
        })
        ctx = resolver.resolve(event)
        assert ctx.user_type == "platform"
        assert ctx.role == "platform-super-admin"
        assert ctx.tenant_id is None
        assert "tenant:delete" in ctx.effective_permissions
        assert "platform:deploy" in ctx.effective_permissions

    @patch("bbws_auth.resolver.boto3")
    def test_resolves_platform_viewer(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "viewer-sub",
            "email": "viewer@bbws.co.za",
            "custom:user_type": "platform",
            "cognito:groups": "[platform-viewer]",
        })
        ctx = resolver.resolve(event)
        assert ctx.role == "platform-viewer"
        assert "tenant:read" in ctx.effective_permissions
        assert "tenant:create" not in ctx.effective_permissions

    @patch("bbws_auth.resolver.boto3")
    def test_highest_precedence_wins(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "multi-sub",
            "email": "multi@bbws.co.za",
            "custom:user_type": "platform",
            "cognito:groups": "[platform-viewer, platform-admin]",
        })
        ctx = resolver.resolve(event)
        assert ctx.role == "platform-admin"

    @patch("bbws_auth.resolver.boto3")
    def test_no_groups_raises_forbidden(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "no-group-sub",
            "email": "nogroup@bbws.co.za",
            "custom:user_type": "platform",
            "cognito:groups": "",
        })
        with pytest.raises(ForbiddenError, match="no recognized Cognito groups"):
            resolver.resolve(event)


class TestResolverTenant:
    """Test tenant user resolution (DynamoDB mocked)."""

    @patch("bbws_auth.resolver.boto3")
    def test_resolves_tenant_editor(self, mock_boto3):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        # Mock user role assignment
        mock_table.get_item.side_effect = [
            {
                "Item": {
                    "role": "editor",
                    "permission_overrides": {"grant": [], "revoke": []},
                }
            },
            {
                "Item": {
                    "permissions": [
                        "site:create", "site:read", "site:edit",
                        "site:stage", "site:deploy",
                        "folder:create", "folder:read", "folder:edit",
                    ]
                }
            },
        ]

        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "tenant-user-sub",
            "email": "user@tenant.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "tenant-abc-123",
            "cognito:groups": "",
        })
        ctx = resolver.resolve(event)
        assert ctx.user_type == "tenant"
        assert ctx.tenant_id == "tenant-abc-123"
        assert ctx.role == "editor"
        assert "site:create" in ctx.effective_permissions
        assert "site:delete" not in ctx.effective_permissions

    @patch("bbws_auth.resolver.boto3")
    def test_grant_override_adds_permission(self, mock_boto3):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        mock_table.get_item.side_effect = [
            {
                "Item": {
                    "role": "editor",
                    "permission_overrides": {"grant": ["site:delete"], "revoke": []},
                }
            },
            {
                "Item": {
                    "permissions": ["site:create", "site:read", "site:edit"]
                }
            },
        ]

        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "user-with-grant",
            "email": "user@tenant.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "tenant-abc",
            "cognito:groups": "",
        })
        ctx = resolver.resolve(event)
        assert "site:delete" in ctx.effective_permissions

    @patch("bbws_auth.resolver.boto3")
    def test_revoke_override_removes_permission(self, mock_boto3):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        mock_table.get_item.side_effect = [
            {
                "Item": {
                    "role": "admin",
                    "permission_overrides": {"grant": [], "revoke": ["site:deploy"]},
                }
            },
            {
                "Item": {
                    "permissions": ["site:create", "site:read", "site:deploy"]
                }
            },
        ]

        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "user-with-revoke",
            "email": "user@tenant.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "tenant-xyz",
            "cognito:groups": "",
        })
        ctx = resolver.resolve(event)
        assert "site:deploy" not in ctx.effective_permissions
        assert "site:create" in ctx.effective_permissions

    @patch("bbws_auth.resolver.boto3")
    def test_no_user_record_raises_forbidden(self, mock_boto3):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {}

        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "unknown-user",
            "email": "unknown@tenant.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "tenant-abc",
            "cognito:groups": "",
        })
        with pytest.raises(ForbiddenError, match="No role assignment found"):
            resolver.resolve(event)

    @patch("bbws_auth.resolver.boto3")
    def test_missing_tenant_id_raises_unauthorized(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "user-no-tenant",
            "email": "user@example.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "",
            "cognito:groups": "",
        })
        with pytest.raises(UnauthorizedError, match="missing custom:tenant_id"):
            resolver.resolve(event)


class TestResolverEdgeCases:
    """Test edge cases."""

    @patch("bbws_auth.resolver.boto3")
    def test_missing_user_type_raises_unauthorized(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "user-1",
            "email": "user@example.com",
            "cognito:groups": "",
        })
        with pytest.raises(UnauthorizedError, match="Missing custom:user_type"):
            resolver.resolve(event)

    @patch("bbws_auth.resolver.boto3")
    def test_unknown_user_type_raises_unauthorized(self, mock_boto3):
        resolver = PermissionResolver()
        event = make_v2_event({
            "sub": "user-1",
            "email": "user@example.com",
            "custom:user_type": "alien",
            "cognito:groups": "",
        })
        with pytest.raises(UnauthorizedError, match="Unknown user_type: alien"):
            resolver.resolve(event)
