"""
TDD: Verify bbws_auth reads from 'tenants' table with uppercase PK/SK.
REM-3.1 — PermissionResolver must use the consolidated tenants table.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

SRC_DIR = Path(__file__).parent.parent.parent / "src" / "bbws_auth"


class TestTableNameConsolidation:
    """Verify all references use 'tenants' table, not 'tenant_permissions'."""

    def test_resolver_default_table_is_tenants(self):
        """PermissionResolver default table must be 'tenants'."""
        content = (SRC_DIR / "resolver.py").read_text()
        # Find the default parameter value
        match = re.search(r'def __init__\(self,\s*table_name:\s*str\s*=\s*"([^"]+)"', content)
        assert match, "Could not find __init__ default table_name"
        assert match.group(1) == "tenants", (
            f"Default table is '{match.group(1)}', expected 'tenants'. "
            f"tenant_permissions is deprecated."
        )

    def test_decorator_default_table_is_tenants(self):
        """require_permission decorator default must be 'tenants'."""
        content = (SRC_DIR / "decorators.py").read_text()
        match = re.search(r'table_name:\s*str\s*=\s*"([^"]+)"', content)
        assert match, "Could not find table_name default in decorators.py"
        assert match.group(1) == "tenants", (
            f"Decorator default table is '{match.group(1)}', expected 'tenants'."
        )


class TestUppercaseKeys:
    """Verify DynamoDB queries use uppercase PK/SK keys."""

    def test_resolver_uses_uppercase_pk_sk(self):
        """resolver.py must use 'PK' and 'SK', not 'pk' and 'sk'."""
        content = (SRC_DIR / "resolver.py").read_text()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if "get_item" in line or "Key={" in line or "Key =" in line:
                continue
            if '"pk"' in line and "TENANT#" in line:
                assert False, (
                    f"resolver.py:{i} uses lowercase 'pk'. Must use 'PK' (uppercase). "
                    f"Line: {line.strip()}"
                )
            if '"sk"' in line and ("USER#" in line or "ROLE#" in line):
                assert False, (
                    f"resolver.py:{i} uses lowercase 'sk'. Must use 'SK' (uppercase). "
                    f"Line: {line.strip()}"
                )

    def test_data_access_uses_uppercase_pk(self):
        """data_access.py must use Key('PK'), not Key('pk')."""
        content = (SRC_DIR / "data_access.py").read_text()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if 'Key("pk")' in stripped or "Key('pk')" in stripped:
                assert False, (
                    f"data_access.py:{i} uses lowercase Key('pk'). Must use Key('PK'). "
                    f"Line: {stripped}"
                )

    @patch("bbws_auth.resolver.boto3")
    def test_get_item_called_with_uppercase_keys(self, mock_boto3):
        """Verify the actual DynamoDB call uses uppercase PK/SK."""
        from bbws_auth.resolver import PermissionResolver
        from tests.unit.conftest import make_v2_event

        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table
        mock_table.get_item.side_effect = [
            {"Item": {"role": "editor", "permission_overrides": {"grant": [], "revoke": []}}},
            {"Item": {"permissions": ["site:read"]}},
        ]

        resolver = PermissionResolver(table_name="tenants")
        event = make_v2_event({
            "sub": "user-1",
            "email": "user@test.com",
            "custom:user_type": "tenant",
            "custom:tenant_id": "t-123",
            "cognito:groups": "",
        })
        resolver.resolve(event)

        # Verify first call (user record) uses uppercase keys
        first_call = mock_table.get_item.call_args_list[0]
        key = first_call[1]["Key"] if "Key" in first_call[1] else first_call[0][0] if first_call[0] else {}
        assert "PK" in key, f"First get_item call uses wrong key names: {key}"
        assert "SK" in key, f"First get_item call uses wrong key names: {key}"
        assert key["PK"] == "TENANT#t-123"
        assert key["SK"] == "USER#user-1"

        # Verify second call (role record) uses uppercase keys
        second_call = mock_table.get_item.call_args_list[1]
        key = second_call[1]["Key"] if "Key" in second_call[1] else second_call[0][0] if second_call[0] else {}
        assert "PK" in key, f"Second get_item call uses wrong key names: {key}"
        assert "SK" in key, f"Second get_item call uses wrong key names: {key}"
        assert key["PK"] == "TENANT#t-123"
        assert key["SK"] == "ROLE#editor"
