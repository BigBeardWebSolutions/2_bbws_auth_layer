"""Tests for JWT claim extraction (HTTP API v2 + REST API v1)."""

import pytest

from bbws_auth.claims import _parse_cognito_groups, extract_claims
from bbws_auth.exceptions import UnauthorizedError

from .conftest import make_v1_event, make_v2_event


class TestExtractClaims:
    """Tests for extract_claims()."""

    def test_extracts_claims_from_v2_event(self, platform_claims):
        event = make_v2_event(platform_claims)
        claims = extract_claims(event)
        assert claims["sub"] == "platform-user-sub-001"
        assert claims["email"] == "admin@bigbeard.co.za"

    def test_extracts_claims_from_v1_event(self, platform_claims):
        event = make_v1_event(platform_claims)
        claims = extract_claims(event)
        assert claims["sub"] == "platform-user-sub-001"

    def test_raises_unauthorized_when_no_claims(self):
        event = {"version": "2.0", "requestContext": {"authorizer": {}}}
        with pytest.raises(UnauthorizedError, match="No JWT claims found"):
            extract_claims(event)

    def test_raises_unauthorized_when_empty_event(self):
        with pytest.raises(UnauthorizedError, match="No JWT claims found"):
            extract_claims({})

    def test_normalizes_groups_in_v2_event(self, platform_claims):
        event = make_v2_event(platform_claims)
        claims = extract_claims(event)
        assert isinstance(claims["cognito:groups"], list)
        assert "platform-super-admin" in claims["cognito:groups"]

    def test_normalizes_groups_in_v1_event(self):
        claims_dict = {
            "sub": "user-1",
            "custom:user_type": "platform",
            "cognito:groups": "platform-admin,platform-viewer",
        }
        event = make_v1_event(claims_dict)
        claims = extract_claims(event)
        assert claims["cognito:groups"] == ["platform-admin", "platform-viewer"]


class TestParseCognitoGroups:
    """Tests for _parse_cognito_groups()."""

    def test_bracket_wrapped_string(self):
        assert _parse_cognito_groups("[admin, user]") == ["admin", "user"]

    def test_comma_separated_string(self):
        assert _parse_cognito_groups("admin,user") == ["admin", "user"]

    def test_single_string(self):
        assert _parse_cognito_groups("admin") == ["admin"]

    def test_already_list(self):
        assert _parse_cognito_groups(["admin", "user"]) == ["admin", "user"]

    def test_empty_string(self):
        assert _parse_cognito_groups("") == []

    def test_none(self):
        assert _parse_cognito_groups(None) == []

    def test_bracket_with_spaces(self):
        assert _parse_cognito_groups("[ admin , user ]") == ["admin", "user"]

    def test_single_bracket_wrapped(self):
        assert _parse_cognito_groups("[admin]") == ["admin"]
