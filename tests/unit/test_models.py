"""Tests for TenantContext and EffectivePermissions models."""

import pytest

from bbws_auth.exceptions import ForbiddenError
from bbws_auth.models import EffectivePermissions, TenantContext, UserType


class TestUserType:
    def test_platform_value(self):
        assert UserType.PLATFORM.value == "platform"

    def test_tenant_value(self):
        assert UserType.TENANT.value == "tenant"

    def test_from_string(self):
        assert UserType("platform") == UserType.PLATFORM
        assert UserType("tenant") == UserType.TENANT

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            UserType("unknown")


class TestTenantContext:
    @pytest.fixture
    def ctx(self):
        return TenantContext(
            user_sub="user-001",
            email="user@example.com",
            user_type="tenant",
            tenant_id="tenant-abc",
            role="editor",
            effective_permissions=frozenset(["site:create", "site:read", "site:edit"]),
        )

    def test_is_frozen(self, ctx):
        with pytest.raises(AttributeError):
            ctx.role = "admin"

    def test_has_permission_true(self, ctx):
        assert ctx.has_permission("site:create") is True

    def test_has_permission_false(self, ctx):
        assert ctx.has_permission("site:delete") is False

    def test_require_permission_passes(self, ctx):
        ctx.require_permission("site:create")  # should not raise

    def test_require_permission_raises(self, ctx):
        with pytest.raises(ForbiddenError, match="site:delete"):
            ctx.require_permission("site:delete")

    def test_require_any_permission_passes(self, ctx):
        ctx.require_any_permission("site:delete", "site:create")  # create exists

    def test_require_any_permission_raises(self, ctx):
        with pytest.raises(ForbiddenError, match="None of"):
            ctx.require_any_permission("site:delete", "site:deploy")


class TestEffectivePermissions:
    def test_frozen(self):
        ep = EffectivePermissions(
            role="editor",
            base_permissions=frozenset(["site:read"]),
            granted_overrides=frozenset(),
            revoked_overrides=frozenset(),
            effective=frozenset(["site:read"]),
        )
        with pytest.raises(AttributeError):
            ep.role = "admin"
