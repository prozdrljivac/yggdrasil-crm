import pytest
from fastapi.testclient import TestClient

from src.api import create_app


def test_health_needs_no_services_or_secrets() -> None:
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/api/health", "/openapi.json"])
def test_unexpected_host_is_rejected(path: str) -> None:
    with TestClient(create_app(), base_url="http://untrusted.example") as client:
        response = client.get(path)

    assert response.status_code == 400


def test_generated_openapi_schema_is_available() -> None:
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["info"]["title"] == "YggdrasilCRM API"


def test_openapi_uses_the_health_response_model() -> None:
    with TestClient(create_app(), base_url="http://localhost") as client:
        schema = client.get("/openapi.json").json()

    response_schema = schema["paths"]["/api/health"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert response_schema == {"$ref": "#/components/schemas/Health"}
    assert schema["components"]["schemas"]["Health"]["properties"]["status"]["const"] == "ok"


def test_unknown_route_is_not_exposed() -> None:
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/api/customers")

    assert response.status_code == 404
