"""Module to handle MQTT communication with Odoo"""

import base64
import logging

import requests

LOGGER = logging.getLogger(__name__)


def odoo_onmessage(odoo_base_url: str, odoo_topic_id: int, payload):
    """Proxy payload to Odoo"""
    LOGGER.info("Proxying payload %s to Odoo Subscription %s", payload, odoo_topic_id)
    odoo_sub_url = odoo_base_url + "/mqtt/topics/" + str(odoo_topic_id) + "/on_message"
    if isinstance(payload, bytes):
        payload = base64.b64encode(payload).decode("utf-8")
    LOGGER.debug("Sending Payload to url: %s -> %s", odoo_sub_url, payload)
    response = requests.post(odoo_sub_url, json={"payload": payload}, timeout=2)
    LOGGER.debug("Odoo Response: %s:%s", response, response.text)
