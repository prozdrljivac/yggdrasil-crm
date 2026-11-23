import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tools import keycloak

ROOT = Path(__file__).resolve().parents[2]
STARTUP = ROOT / "infra/keycloak/start-local.sh"


@pytest.fixture
def realm() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ROOT / "infra/keycloak/huginn-muninn-local-realm.json").read_text()
    )
    return data


def test_realm_has_only_distinct_fictional_local_accounts(realm: dict[str, Any]) -> None:
    assert realm["realm"] == keycloak.REALM
    assert realm["registrationAllowed"] is False
    assert realm["identityProviders"] == []
    assert realm["components"] == {}
    users = {user["username"]: user for user in realm["users"]}
    assert set(users) == {"fixture-owner", "fixture-nonowner"}
    assert users["fixture-owner"]["id"] == "7ecb6b4c-d775-4c64-a289-d97bd4184411"
    assert users["fixture-nonowner"]["id"] == "15633bb8-58f9-444d-b14e-6bd3973b7422"
    for user in users.values():
        assert user["email"].endswith("@example.invalid")
        assert user["enabled"] is True
        assert user["requiredActions"] == ["CONFIGURE_TOTP"]
        assert "realmRoles" not in user
        assert user["clientRoles"] == {"account": ["manage-account", "view-profile"]}
        assert user["credentials"][0]["value"].startswith("${LOCAL_")


def test_fixture_browser_flow_requires_password_and_otp(realm: dict[str, Any]) -> None:
    flow = next(
        flow for flow in realm["authenticationFlows"] if flow["alias"] == realm["browserFlow"]
    )
    executions = flow["authenticationExecutions"]
    assert [(item["authenticator"], item["requirement"]) for item in executions] == [
        ("auth-username-password-form", "REQUIRED"),
        ("auth-otp-form", "REQUIRED"),
    ]
    assert realm["requiredActions"][0]["enabled"] is True
    assert realm["requiredActions"][0]["defaultAction"] is True
    assert realm["otpPolicyType"] == "totp"
    assert realm["otpPolicyCodeReusable"] is False


def test_crm_client_is_confidential_and_cannot_yet_redirect_to_the_crm(
    realm: dict[str, Any],
) -> None:
    assert len(realm["clients"]) == 1
    client = realm["clients"][0]
    assert client["clientId"] == "yggdrasil-crm"
    assert client["publicClient"] is False
    assert client["clientAuthenticatorType"] == "client-secret"
    assert client["attributes"]["pkce.code.challenge.method"] == "S256"
    assert client["standardFlowEnabled"] is True
    assert client["implicitFlowEnabled"] is False
    assert client["directAccessGrantsEnabled"] is False
    assert client["serviceAccountsEnabled"] is False
    assert client["redirectUris"] == []
    assert client["webOrigins"] == []


@pytest.mark.parametrize(
    "value",
    [
        "",
        "short",
        'fictional-quote"-injection',
        "fictional-backslash\\injection",
        "fictional-${EXPANSION}",
        "fictional-control\ncharacter",
    ],
)
def test_startup_rejects_unsafe_import_values_without_echoing_them(value: str) -> None:
    environment = {
        **os.environ,
        "LOCAL_OWNER_PASSWORD": value,
        "LOCAL_NONOWNER_PASSWORD": "fictional-valid-nonowner",
        "LOCAL_CRM_CLIENT_SECRET": "fictional-valid-client",
    }
    result = subprocess.run(  # noqa: S603 -- Fixed local validator script; fictional environment only.
        ["/bin/bash", str(STARTUP)],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "LOCAL_OWNER_PASSWORD must contain 16-128 letters, digits, underscores, or hyphens.\n"
    )


@pytest.mark.parametrize(
    "binding",
    [
        "0.0.0.0:8081",
        "localhost:8081",
        "127.0.0.1:0",
        "127.0.0.1:65536",
        "127.0.0.1:8081\n0.0.0.0:8081",
    ],
)
def test_discovery_tool_rejects_nonlocal_or_invalid_bindings(binding: str) -> None:
    with pytest.raises(ValueError):
        keycloak.local_base_url(binding)


@pytest.mark.parametrize("server_time", [70, 100, 131])
def test_clock_check_allows_small_skew_and_command_latency(server_time: int) -> None:
    keycloak.validate_clock(server_time, 100, 101)


@pytest.mark.parametrize("server_time", [69, 132])
def test_clock_check_rejects_skew_that_can_break_mfa(server_time: int) -> None:
    with pytest.raises(RuntimeError, match="Resynchronize Docker Desktop"):
        keycloak.validate_clock(server_time, 100, 101)


def test_discovery_tool_uses_the_configured_loopback_port() -> None:
    assert keycloak.local_base_url("127.0.0.1:18081") == "http://127.0.0.1:18081"


def test_discovery_requires_exact_local_urls_and_s256() -> None:
    issuer = f"http://127.0.0.1:18081/realms/{keycloak.REALM}"
    valid: dict[str, Any] = {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "code_challenge_methods_supported": ["S256"],
    }
    keycloak.validate_discovery(valid, issuer)
    for field in ["issuer", "authorization_endpoint", "token_endpoint"]:
        with pytest.raises(ValueError):
            keycloak.validate_discovery({**valid, field: "http://untrusted.invalid"}, issuer)
    with pytest.raises(ValueError):
        keycloak.validate_discovery(
            {**valid, "code_challenge_methods_supported": ["plain"]}, issuer
        )


@pytest.fixture
def reset_project() -> dict[str, Any]:
    return {
        "name": "fictional-local",
        "services": {
            "keycloak": {
                "volumes": [
                    {"type": "volume", "source": "keycloak_data", "target": "/opt/keycloak/data"},
                ]
            },
            "postgres": {
                "volumes": [
                    {"type": "volume", "source": "postgres_data", "target": "/var/lib/postgresql"},
                ]
            },
        },
        "volumes": {
            "keycloak_data": {"name": "fictional-local_keycloak_data"},
            "postgres_data": {"name": "fictional-local_postgres_data"},
        },
    }


def test_reset_selects_only_keycloak_volume(reset_project: dict[str, Any]) -> None:
    assert keycloak.keycloak_data_volume(reset_project) == "fictional-local_keycloak_data"


def test_reset_rejects_external_volume(reset_project: dict[str, Any]) -> None:
    reset_project["volumes"]["keycloak_data"]["external"] = True
    with pytest.raises(ValueError):
        keycloak.keycloak_data_volume(reset_project)


def test_reset_rejects_a_nonstandard_volume_name(reset_project: dict[str, Any]) -> None:
    reset_project["volumes"]["keycloak_data"]["name"] = "unrelated-data"
    with pytest.raises(ValueError):
        keycloak.keycloak_data_volume(reset_project)


def test_reset_rejects_shared_volume(reset_project: dict[str, Any]) -> None:
    reset_project["volumes"]["postgres_data"]["name"] = "fictional-local_keycloak_data"
    with pytest.raises(ValueError):
        keycloak.keycloak_data_volume(reset_project)


def test_reset_requires_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["keycloak.py", "reset"])

    def unexpected_docker(*arguments: str) -> str:
        pytest.fail("Unconfirmed reset must not call Docker.")

    monkeypatch.setattr(keycloak, "docker", unexpected_docker)
    with pytest.raises(SystemExit) as error:
        keycloak.main()
    assert error.value.code == 2


def test_reset_does_not_touch_other_containers_or_volumes(
    reset_project: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[tuple[str, ...]] = []

    def fake_docker(*arguments: str) -> str:
        commands.append(arguments)
        if arguments == ("compose", "config", "--format", "json"):
            return json.dumps(reset_project)
        return ""

    monkeypatch.setattr(keycloak, "docker", fake_docker)
    keycloak.reset_keycloak()

    assert commands == [
        ("compose", "config", "--format", "json"),
        ("compose", "stop", "keycloak"),
        ("compose", "rm", "--force", "keycloak"),
        ("volume", "rm", "fictional-local_keycloak_data"),
        ("compose", "up", "--detach", "--no-deps", "--wait", "--wait-timeout", "180", "keycloak"),
    ]


def test_unsafe_reset_fails_before_mutating_infrastructure(
    reset_project: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    project = copy.deepcopy(reset_project)
    project["volumes"]["keycloak_data"]["external"] = True
    commands: list[tuple[str, ...]] = []

    def fake_docker(*arguments: str) -> str:
        commands.append(arguments)
        return json.dumps(project)

    monkeypatch.setattr(keycloak, "docker", fake_docker)
    with pytest.raises(ValueError):
        keycloak.reset_keycloak()
    assert commands == [("compose", "config", "--format", "json")]
