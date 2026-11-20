"""Read configuration from the environment, not from Doppler's API."""

from urllib.parse import quote

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YGGDRASIL_", hide_input_in_errors=True)

    rabbitmq_user: str = Field(min_length=1)
    rabbitmq_password: SecretStr = Field(min_length=1)
    rabbitmq_vhost: str = Field(min_length=1)
    rabbitmq_port: int = Field(ge=1, le=65535)

    @property
    def broker_url(self) -> SecretStr:
        user = quote(self.rabbitmq_user, safe="")
        password = quote(self.rabbitmq_password.get_secret_value(), safe="")
        vhost = quote(self.rabbitmq_vhost, safe="")
        return SecretStr(f"amqp://{user}:{password}@127.0.0.1:{self.rabbitmq_port}/{vhost}")
