"""Datamodels for MQTT Proxy"""
import re
from logging import getLogger

from pydantic import BaseModel, Field, field_validator

LOGGER = getLogger(__name__)


class Subscribtion(BaseModel):
    """MQTT Subscription"""

    topic: str
    odoo_id: int
    client_id: int
    mid: tuple[int, int] = None


class MQTTClientArgs(BaseModel):
    """MQTT Client Arguments"""

    odoo_id: int
    odoo_base_url: str
    odoo_mqtt_token: str
    odoo_user_id: int
    mqtt_host: str
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = Field("", repr=False)
    subscriptions: list[Subscribtion] = []

    # pydantic validation to check valid url schema on odoo_base_url

    @field_validator("odoo_base_url")
    @classmethod
    def check_odoo_base_url(cls, url: str) -> str:
        """Checks if odoo_base_url is a valid url"""
        regex_url_scheme = re.compile(r"^(http|https)://")
        if not regex_url_scheme.match(url):
            raise ValueError("odoo_base_url must start with http or https")
        return url


class MQTTThreadStatus(BaseModel):
    """MQTT Thread Status"""

    thread_id: int
    thread_running: bool
    client_connected: bool = False
