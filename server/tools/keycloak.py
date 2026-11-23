"""Local Keycloak discovery and an explicitly confirmed, volume-scoped reset."""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
REALM = "huginn-muninn-local"
MAX_CLOCK_SKEW_SECONDS = 30


def docker(*arguments: str) -> str:
    executable = shutil.which("docker")
    if executable is None:
        raise RuntimeError("Docker CLI is required.")

    result = subprocess.run(  # noqa: S603 -- Fixed Docker operations; no shell or credential arguments.
        [executable, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Docker command failed. Check local infrastructure configuration and logs."
        )
    return result.stdout.strip()


def local_base_url(binding: str) -> str:
    host, separator, port = binding.partition(":")
    if host != "127.0.0.1" or separator != ":" or not port.isdecimal():
        raise ValueError("Keycloak must publish one IPv4 loopback port.")
    if not 1 <= int(port) <= 65535:
        raise ValueError("Invalid Keycloak host port.")
    return f"http://127.0.0.1:{int(port)}"


def validate_discovery(document: dict[str, Any], issuer: str) -> None:
    expected = {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
    }
    if any(document.get(key) != value for key, value in expected.items()):
        raise ValueError("Keycloak discovery does not match the local issuer.")
    if "S256" not in document.get("code_challenge_methods_supported", []):
        raise ValueError("Keycloak must support S256 PKCE.")


def validate_clock(server_time: int, host_before: float, host_after: float) -> None:
    if (
        server_time < host_before - MAX_CLOCK_SKEW_SECONDS
        or server_time > host_after + MAX_CLOCK_SKEW_SECONDS
    ):
        raise RuntimeError(
            "Docker and host clocks differ by more than 30 seconds. "
            "Resynchronize Docker Desktop before testing MFA; do not widen the OTP window."
        )


def check_keycloak() -> None:
    before = time.time()
    server_time = int(docker("compose", "exec", "-T", "keycloak", "date", "+%s"))
    validate_clock(server_time, before, time.time())
    base_url = local_base_url(docker("compose", "port", "keycloak", "8080"))
    issuer = f"{base_url}/realms/{REALM}"
    with httpx.Client(timeout=10, trust_env=False) as client:
        response = client.get(f"{issuer}/.well-known/openid-configuration")
        response.raise_for_status()
        validate_discovery(response.json(), issuer)
    print("Local Keycloak discovery passed. Run the separate browser login and MFA checks.")


def keycloak_data_volume(project: dict[str, Any]) -> str:
    service = project["services"]["keycloak"]
    volumes = project["volumes"]
    definition = volumes["keycloak_data"]
    expected_name = f"{project['name']}_keycloak_data"
    data_mounts = [mount for mount in service["volumes"] if mount["target"] == "/opt/keycloak/data"]
    if (
        definition.get("external")
        or definition.get("name") != expected_name
        or len(data_mounts) != 1
        or data_mounts[0].get("type") != "volume"
        or data_mounts[0].get("source") != "keycloak_data"
    ):
        raise ValueError("Reset requires a dedicated, Compose-managed Keycloak data volume.")

    for name, other in project["services"].items():
        if name == "keycloak":
            continue
        for mount in other.get("volumes", []):
            source = mount.get("source")
            if mount.get("type") == "volume" and volumes[source].get("name") == expected_name:
                raise ValueError("Refusing to reset a volume shared with another service.")
    return expected_name


def reset_keycloak() -> None:
    volume = keycloak_data_volume(json.loads(docker("compose", "config", "--format", "json")))
    docker("compose", "stop", "keycloak")
    docker("compose", "rm", "--force", "keycloak")
    docker("volume", "rm", volume)
    docker("compose", "up", "--detach", "--no-deps", "--wait", "--wait-timeout", "180", "keycloak")
    print("Only local Keycloak data was reset. Enroll MFA again for both fictional accounts.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "reset"])
    parser.add_argument("--confirm-reset", action="store_true")
    arguments = parser.parse_args()
    if arguments.action == "reset" and not arguments.confirm_reset:
        parser.error(
            "Reset deletes local Keycloak accounts, sessions, and MFA. Add --confirm-reset."
        )

    try:
        if arguments.action == "check":
            check_keycloak()
        else:
            reset_keycloak()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    except ValueError, KeyError, TypeError, httpx.HTTPError:
        print(
            "Keycloak operation failed. Check local configuration and service logs.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
