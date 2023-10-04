"""Module to handle MQTT communication with Odoo"""

import base64
import logging

import requests

LOGGER = logging.getLogger(__name__)


def odoo_check_connection(odoo_base_url: str, odoo_auth_token: str) -> bool:
    """Check if connection to Odoo is possible"""
    LOGGER.debug("Checking connection to Odoo")
    odoo_url = odoo_base_url + "/mqtt/check"
    LOGGER.debug("Sending Request to url: %s", odoo_url)
    response = requests.get(odoo_url, headers={"X-MQTT-Auth-Token": odoo_auth_token}, timeout=10)
    LOGGER.debug("Odoo Response: %s:%s", response, response.text)
    if response.status_code == 200:
        return True
    LOGGER.warning("Check OdooConnect: Response: %s:%s", response, response.text)
    return False


def odoo_onmessage(odoo_base_url: str, odoo_topic_id: int, odoo_auth_token: str, payload):
    """Proxy payload to Odoo"""
    LOGGER.info("Proxying payload to Odoo Subscription %s", odoo_topic_id)
    odoo_sub_url = odoo_base_url + "/mqtt/topics/" + str(odoo_topic_id) + "/on_message"
    if isinstance(payload, bytes):
        payload = base64.b64encode(payload).decode("utf-8")
    LOGGER.debug("Sending Payload to url: %s", odoo_sub_url)
    try:
        response = requests.post(
            odoo_sub_url,
            json={"payload": payload},
            headers={"X-MQTT-Auth-Token": odoo_auth_token},
            timeout=60,
        )
        LOGGER.debug("Odoo Response: %s:%s", response, response.text)
        if response.status_code == 200:
            return True
        LOGGER.warning("Odoo onMessage Response: %s:%s", response, response.text)
        return False
    except requests.exceptions.ConnectionError as err:
        LOGGER.warning("Odoo onMessage ConnectionError: %s", err)
        return False
