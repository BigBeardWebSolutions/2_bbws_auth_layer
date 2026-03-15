"""Tests for platform permission map."""

from bbws_auth.platform_permissions import (
    PLATFORM_PERMISSION_MAP,
    PLATFORM_ROLE_PRECEDENCE,
    highest_platform_role,
)


class TestPlatformPermissionMap:
    def test_four_roles_defined(self):
        assert len(PLATFORM_PERMISSION_MAP) == 4

    def test_super_admin_has_all_permissions(self):
        perms = PLATFORM_PERMISSION_MAP["platform-super-admin"]
        assert "tenant:create" in perms
        assert "tenant:delete" in perms
        assert "platform:configure" in perms
        assert "platform:deploy" in perms
        assert "audit:read" in perms

    def test_viewer_has_read_only(self):
        perms = PLATFORM_PERMISSION_MAP["platform-viewer"]
        assert "tenant:read" in perms
        assert "monitoring:read" in perms
        assert "audit:read" in perms
        assert "tenant:create" not in perms
        assert "user:invite" not in perms

    def test_admin_cannot_delete_tenants(self):
        perms = PLATFORM_PERMISSION_MAP["platform-admin"]
        assert "tenant:delete" not in perms

    def test_operator_cannot_write(self):
        perms = PLATFORM_PERMISSION_MAP["platform-operator"]
        assert "tenant:create" not in perms
        assert "user:invite" not in perms
        assert "billing:edit" not in perms

    def test_permissions_are_frozensets(self):
        for role, perms in PLATFORM_PERMISSION_MAP.items():
            assert isinstance(perms, frozenset), f"{role} permissions not frozenset"


class TestHighestPlatformRole:
    def test_super_admin_wins(self):
        groups = ["platform-viewer", "platform-super-admin", "platform-admin"]
        assert highest_platform_role(groups) == "platform-super-admin"

    def test_admin_over_operator(self):
        groups = ["platform-operator", "platform-admin"]
        assert highest_platform_role(groups) == "platform-admin"

    def test_single_group(self):
        assert highest_platform_role(["platform-viewer"]) == "platform-viewer"

    def test_no_recognized_groups(self):
        assert highest_platform_role(["some-other-group"]) is None

    def test_empty_groups(self):
        assert highest_platform_role([]) is None

    def test_precedence_order(self):
        assert PLATFORM_ROLE_PRECEDENCE[0] == "platform-super-admin"
        assert PLATFORM_ROLE_PRECEDENCE[-1] == "platform-viewer"
