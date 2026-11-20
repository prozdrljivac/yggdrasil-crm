from urllib.parse import unquote, urlsplit

import pytest
from pydantic import ValidationError

from src.background import create_worker
from src.config import Settings


@pytest.fixture
def broker_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_USER", "fictional")
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_PASSWORD", "local-only")
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_VHOST", "test")
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_PORT", "5673")


def test_configuration_reads_shared_values_and_redacts_credentials(broker_env: None) -> None:
    settings = Settings()

    assert settings.broker_url.get_secret_value() == (
        "amqp://fictional:local-only@127.0.0.1:5673/test"
    )
    assert "local-only" not in repr(settings)
    assert "local-only" not in str(settings.broker_url)


def test_broker_url_encodes_credentials_and_vhost(
    broker_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_USER", "user@local")
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_PASSWORD", "fictional:$ /@")
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_VHOST", "/")

    url = urlsplit(Settings().broker_url.get_secret_value())

    assert unquote(url.username or "") == "user@local"
    assert unquote(url.password or "") == "fictional:$ /@"
    assert url.path == "/%2F"
    assert url.hostname == "127.0.0.1"
    assert url.port == 5673


@pytest.mark.parametrize("field", ["USER", "PASSWORD", "VHOST", "PORT"])
def test_missing_broker_setting_is_rejected(
    broker_env: None, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    monkeypatch.delenv(f"YGGDRASIL_RABBITMQ_{field}")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("port", ["0", "65536", "invalid-port"])
def test_invalid_port_is_rejected_without_echoing_input(
    broker_env: None, monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("YGGDRASIL_RABBITMQ_PORT", port)

    with pytest.raises(ValidationError) as error:
        Settings()

    assert "input_value" not in str(error.value)


@pytest.mark.parametrize("field", ["USER", "PASSWORD", "VHOST"])
def test_empty_broker_setting_is_rejected(
    broker_env: None, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    monkeypatch.setenv(f"YGGDRASIL_RABBITMQ_{field}", "")

    with pytest.raises(ValidationError):
        Settings()


def test_worker_accepts_only_json_without_connecting_to_rabbitmq(broker_env: None) -> None:
    settings = Settings()
    worker = create_worker(settings)

    assert worker.conf.broker_url == settings.broker_url.get_secret_value()
    assert worker.conf.accept_content == ["json"]
    assert worker.conf.task_serializer == "json"
    assert worker.conf.result_serializer == "json"
    assert worker.conf.task_ignore_result is True
    assert worker.conf.result_backend is None
