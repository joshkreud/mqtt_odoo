"""MQTT Thread wrapper around paho mqtt client"""
import threading
import time
from logging import getLogger

import paho.mqtt.client as mqtt

from .models import MQTTClientArgs, Subscribtion
from .odoo import odoo_check_connection, odoo_onmessage


class MQTTThread(threading.Thread):
    """MQTT Thread wrapper around paho mqtt client"""

    def __init__(self, client_args: MQTTClientArgs):
        threading.Thread.__init__(self)
        self.client_args = client_args
        self.client = mqtt.Client()
        self.name = f"MQTTThread-{self.client_args.odoo_id}"
        self.logger = getLogger(self.name)
        self.logger.info("Creating MQTT Thread for %s", client_args)
        self.daemon = True
        self.running = False
        self.connected = False
        self.connecting = False
        self.subscriptions: dict[int, Subscribtion] = {}  # {subscription_id: Subscribtion}

        # Set Callbacks
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_connect_fail = self.on_connect_fail
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log

    def subscription_by_mid(self, mid: int) -> Subscribtion:
        """Return a subscription by mid

        Parameters
        ----------
        mid : int
            mid, as passed to callbacks

        Returns
        -------
        Subscribtion
        """
        for subscription in self.subscriptions.values():
            if subscription.mid == mid:
                return subscription
        self.logger.warning("Subscription with mid '%s' not found", mid)
        raise KeyError(f"Subscription with mid '{mid}' not found")

    def add_subscription(self, subscription: Subscribtion):
        """Adds a subscription to the client

        Parameters
        ----------
        subscription : Subscribtion
            subscribtion to add
        """
        self.logger.info("MQTT Client %s Adding subscription %s", self.client_args.odoo_id, subscription)
        result, subscription.mid = self.client.subscribe(subscription.topic)
        if not result == 0:
            self.logger.warning("Subscription failed with result code %s", result)
            raise ConnectionError(f"Subscription failed with result code {result}")
        self.subscriptions[subscription.odoo_id] = subscription

    def remove_subscription(self, subscription_id: int):
        """Removes a subscription from the client

        Parameters
        ----------
        subscription_id : int
            id of the subscription to remove
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            self.logger.warning("Subscription with id %s not found", subscription_id)
            raise KeyError(f"Subscription {subscription_id} not found in thread {self.client_args}")
        self.logger.info("MQTT Client %s Removing subscription %s", self.client_args.odoo_id, subscription)
        self.client.unsubscribe(subscription.topic)
        del subscription

    # ==========================================================================
    # Paho-MQTT Callbacks
    # ==========================================================================

    def on_log(self, client, userdata, level, buf):  # pylint: disable=unused-argument,invalid-name
        """Paho-Mqtt Callback function for MQTT Log"""
        self.logger.debug("MQTT Log: Level=%s Buf=%s", level, buf)

    def on_connect(self, client, userdata, flags, rc):  # pylint: disable=unused-argument,invalid-name
        """Paho-Mqtt Callback function for MQTT Connect"""
        self.logger.info("Connected with result code %s", rc)
        self.connecting = False
        if rc == 0:
            self.connected = True
            for subscription in self.client_args.subscriptions:
                self.add_subscription(subscription)
        else:
            self.logger.warning("MQTT Connection failed with result code %s", rc)

    def on_connect_fail(self, client, userdata, rc):  # pylint: disable=unused-argument,invalid-name
        """Patho-Mqtt Callback function for MQTT Connect Fail"""
        self.logger.warning("MQTT Connection failed with rc=%s", rc)

    def on_disconnect(self, client, userdata, rc):  # pylint: disable=unused-argument,invalid-name
        """Callback function for MQTT Disconnect"""
        self.logger.info("MQTT Client Disconnected with result code %s", rc)
        self.connected = False

    def on_message(self, client, userdata, msg):  # pylint: disable=unused-argument
        """Paho-Mqtt Callback function for MQTT Message"""
        self.logger.info("Message received on topic %s", msg.topic)
        self.logger.debug("Message Payload: %s", msg.payload)
        subscriptions = [sub for sub in self.subscriptions.values() if sub.topic == msg.topic]
        for subscription in subscriptions:
            try:
                odoo_onmessage(
                    odoo_base_url=self.client_args.odoo_base_url,
                    odoo_topic_id=subscription.odoo_id,
                    odoo_auth_token=self.client_args.odoo_mqtt_token,
                    payload=msg.payload,
                )
            except Exception as error:  # pylint: disable=broad-except
                self.logger.exception("Error while sending message to odoo: %s", error)

    def on_subscribe(self, client, userdata, mid, granted_qos):  # pylint: disable=unused-argument
        """Patho-Mqtt Callback function for MQTT Subscribe"""
        sub = self.subscription_by_mid(mid)
        self.logger.info("MQTT on_subscribe: topic=%s granted_qos=%s", sub.topic if sub else mid, granted_qos)

    def on_unsubscribe(self, client, userdata, mid):  # pylint: disable=unused-argument,invalid-name
        """Paho-Mqtt Callback function for MQTT Unsubscribe"""
        sub = self.subscription_by_mid(mid)
        self.logger.info("MQTT Unsubscribed from Topic: %s", sub.topic if sub else mid)

    # ==========================================================================
    # Thread Control
    # We control the Thread by ourself
    # ==========================================================================

    def connect(self):
        """Connect MQTT Client"""
        if self.client_args.mqtt_username and self.client_args.mqtt_password:
            self.logger.debug("Setting MQTT Credentials")
            self.client.username_pw_set(self.client_args.mqtt_username, self.client_args.mqtt_password)
        self.logger.info("Connecting to MQTT Broker: %s", self.client_args.mqtt_host)
        self.client.connect(self.client_args.mqtt_host, self.client_args.mqtt_port)
        self.connecting = True
        time.sleep(1)

    def run(self):
        """Gets called when thread starts"""
        self.running = True
        while self.running:
            if not self.connected and not self.connecting:
                self.connect()
            else:
                self.client.loop_read()
                self.client.loop_write()
                self.client.loop_misc()
                time.sleep(0.5)

    def start(self):
        """Starts the thread. blocks until thread is running or timeout is reached to avoid race conditions"""
        self.logger.info("Starting MQTT Thread: %s", self.client_args.odoo_id)
        super().start()
        # Hold until Thread is reported running
        timeout = 2
        curr_time = time.time()
        while not self.running and time.time() < curr_time + timeout:
            time.sleep(0.5)

        # Check if the Callback Works
        if not odoo_check_connection(self.client_args.odoo_base_url, self.client_args.odoo_mqtt_token):
            self.logger.exception("Odoo Connection Check failed. Stopping MQTT Thread %s", self.client_args.odoo_id)
            self.stop()

    def stop(self):
        """Gets called when thread stops"""
        self.logger.info("Stopping MQTT Thread %s", self.client_args.odoo_id)
        self.running = False
        self.client.disconnect()
