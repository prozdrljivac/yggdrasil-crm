import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / ".env.example"


def compose_config(
    env_file: Path | None = EXAMPLE,
    overrides: dict[str, str] | None = None,
    directory: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker CLI is required for Compose configuration checks")

    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("YGGDRASIL_", "COMPOSE_"))
    }
    environment.update(overrides or {})
    command = [docker, "compose"]
    if env_file is not None:
        command.extend(["--env-file", str(env_file)])
    command.extend(["config", "--format", "json"])
    return subprocess.run(  # noqa: S603 -- Fixed Docker command, with fictional test settings only.
        command,
        cwd=directory,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def configured_services(overrides: dict[str, str] | None = None) -> dict[str, Any]:
    result = compose_config(overrides=overrides)
    assert result.returncode == 0, result.stderr
    services: dict[str, Any] = json.loads(result.stdout)["services"]
    return services


def test_compose_automatically_uses_local_env_not_example(tmp_path: Path) -> None:
    (tmp_path / "compose.yaml").write_text((ROOT / "compose.yaml").read_text())
    (tmp_path / ".env.example").write_text(EXAMPLE.read_text())
    (tmp_path / ".env").write_text(
        EXAMPLE.read_text().replace(
            "YGGDRASIL_RABBITMQ_USER=yggdrasil_local",
            "YGGDRASIL_RABBITMQ_USER=fictional_local_override",
        )
    )

    result = compose_config(env_file=None, directory=tmp_path)

    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]
    assert services["rabbitmq"]["environment"]["RABBITMQ_DEFAULT_USER"] == (
        "fictional_local_override"
    )


def test_compose_does_not_fall_back_to_example_when_env_is_missing(tmp_path: Path) -> None:
    (tmp_path / "compose.yaml").write_text((ROOT / "compose.yaml").read_text())
    (tmp_path / ".env.example").write_text(EXAMPLE.read_text())

    result = compose_config(env_file=None, directory=tmp_path)

    assert result.returncode != 0
    assert "YGGDRASIL_" in result.stderr


def test_example_configures_only_required_container_variables() -> None:
    services = configured_services({"YGGDRASIL_UNRELATED_SECRET": "fictional-not-for-containers"})

    assert set(services["postgres"]["environment"]) == {
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    }
    assert set(services["rabbitmq"]["environment"]) == {
        "RABBITMQ_DEFAULT_USER",
        "RABBITMQ_DEFAULT_PASS",
        "RABBITMQ_DEFAULT_VHOST",
    }
    assert set(services["seaweedfs"]["environment"]) == {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "S3_BUCKET",
    }
    assert not services["gotenberg"].get("environment")
    assert set(services["keycloak"]["environment"]) == {
        "KC_DB",
        "KC_HOSTNAME",
        "KC_HEALTH_ENABLED",
        "KC_HTTP_MANAGEMENT_SCHEME",
        "KC_BOOTSTRAP_ADMIN_USERNAME",
        "KC_BOOTSTRAP_ADMIN_PASSWORD",
        "LOCAL_OWNER_PASSWORD",
        "LOCAL_NONOWNER_PASSWORD",
        "LOCAL_CRM_CLIENT_SECRET",
    }


def test_custom_credentials_reach_the_matching_containers() -> None:
    services = configured_services(
        {
            "YGGDRASIL_POSTGRES_DB": "fictional_database",
            "YGGDRASIL_POSTGRES_USER": "fictional_postgres",
            "YGGDRASIL_POSTGRES_PASSWORD": "fictional-$postgres:@ /",
            "YGGDRASIL_RABBITMQ_USER": "fictional_rabbit",
            "YGGDRASIL_RABBITMQ_PASSWORD": "fictional-$rabbit:@ /",
            "YGGDRASIL_RABBITMQ_VHOST": "fictional_vhost",
            "YGGDRASIL_S3_ACCESS_KEY": "fictional-key",
            "YGGDRASIL_S3_SECRET_KEY": "fictional-$s3:/@",
            "YGGDRASIL_S3_BUCKET": "fictional-bucket",
        }
    )

    # Compose escapes dollars when rendering config for reuse as Compose input.
    assert services["postgres"]["environment"] == {
        "POSTGRES_DB": "fictional_database",
        "POSTGRES_USER": "fictional_postgres",
        "POSTGRES_PASSWORD": "fictional-$$postgres:@ /",
    }
    assert services["rabbitmq"]["environment"] == {
        "RABBITMQ_DEFAULT_USER": "fictional_rabbit",
        "RABBITMQ_DEFAULT_PASS": "fictional-$$rabbit:@ /",
        "RABBITMQ_DEFAULT_VHOST": "fictional_vhost",
    }
    assert services["seaweedfs"]["environment"] == {
        "AWS_ACCESS_KEY_ID": "fictional-key",
        "AWS_SECRET_ACCESS_KEY": "fictional-$$s3:/@",
        "S3_BUCKET": "fictional-bucket",
    }


def test_custom_ports_keep_loopback_bindings_and_fixed_container_ports() -> None:
    services = configured_services(
        {
            "YGGDRASIL_POSTGRES_PORT": "15432",
            "YGGDRASIL_RABBITMQ_PORT": "15672",
            "YGGDRASIL_RABBITMQ_MANAGEMENT_PORT": "25672",
            "YGGDRASIL_GOTENBERG_PORT": "13000",
            "YGGDRASIL_S3_PORT": "18333",
            "YGGDRASIL_KEYCLOAK_PORT": "18081",
        }
    )
    expected = {
        "postgres": [(5432, "15432")],
        "rabbitmq": [(5672, "15672"), (15672, "25672")],
        "gotenberg": [(3000, "13000")],
        "seaweedfs": [(8333, "18333")],
        "keycloak": [(8080, "18081")],
    }

    for service, ports in expected.items():
        bindings = services[service]["ports"]
        assert [(port["target"], port["published"]) for port in bindings] == ports
        assert all(port["host_ip"] == "127.0.0.1" for port in bindings)
        assert "@sha256:" in services[service]["image"]

    assert services["postgres"]["healthcheck"]["test"][0] == "CMD-SHELL"
    assert "$POSTGRES_USER" in services["postgres"]["healthcheck"]["test"][1]


def test_keycloak_has_private_management_and_read_only_fixture_mounts() -> None:
    service = configured_services({"YGGDRASIL_KEYCLOAK_PORT": "18081"})["keycloak"]
    assert service["environment"]["KC_DB"] == "dev-file"
    assert service["environment"]["KC_HOSTNAME"] == "http://127.0.0.1:18081"
    assert service["environment"]["KC_HEALTH_ENABLED"] == "true"
    assert service["command"] == ["start-dev", "--import-realm"]
    assert [port["target"] for port in service["ports"]] == [8080]
    assert service["healthcheck"]["test"][:2] == ["CMD", "/bin/bash"]
    assert "/dev/tcp/127.0.0.1/9000" in service["healthcheck"]["test"][-1]
    binds = [mount for mount in service["volumes"] if mount["type"] == "bind"]
    assert len(binds) == 2
    assert all(mount["read_only"] for mount in binds)
    assert all(mount.get("bind", {}).get("create_host_path", False) is False for mount in binds)
    assert set(service["networks"]) == {"identity"}


@pytest.mark.parametrize(
    "field", ["ADMIN_PASSWORD", "OWNER_PASSWORD", "NONOWNER_PASSWORD", "CLIENT_SECRET"]
)
def test_missing_keycloak_credentials_fail_closed(field: str) -> None:
    result = compose_config(overrides={f"YGGDRASIL_KEYCLOAK_{field}": ""})
    assert result.returncode != 0
    assert f"YGGDRASIL_KEYCLOAK_{field}" in result.stderr


def test_missing_credential_fails_without_a_fallback(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            line
            for line in EXAMPLE.read_text().splitlines()
            if not line.startswith("YGGDRASIL_POSTGRES_PASSWORD=")
        )
    )

    result = compose_config(env_file)

    assert result.returncode != 0
    assert "YGGDRASIL_POSTGRES_PASSWORD" in result.stderr


def test_empty_credential_fails_without_a_fallback() -> None:
    result = compose_config(overrides={"YGGDRASIL_S3_SECRET_KEY": ""})

    assert result.returncode != 0
    assert "YGGDRASIL_S3_SECRET_KEY" in result.stderr


def test_single_quoted_password_keeps_literal_dollar_signs(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        EXAMPLE.read_text().replace(
            "YGGDRASIL_RABBITMQ_PASSWORD='local-only-rabbitmq-not-a-secret'",
            "YGGDRASIL_RABBITMQ_PASSWORD='fictional-$notAnEnvironmentVariable'",
        )
    )

    result = compose_config(env_file)

    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]
    expected = "fictional-$$notAnEnvironmentVariable"
    assert services["rabbitmq"]["environment"]["RABBITMQ_DEFAULT_PASS"] == expected
