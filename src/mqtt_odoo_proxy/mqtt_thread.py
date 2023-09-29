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
        self.subscriptions: dict[int, Subscribtion] = {}  # {subscription_id: Subscribtion}
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_connect_fail = self.on_connect_fail
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def add_subscription(self, subscription: Subscribtion):
        """Adds a subscription to the client

        Parameters
        ----------
        subscription : Subscribtion
            subscribtion to add
        """
        self.logger.info("MQTT Client %s Adding subscription %s", self.client_args.odoo_id, subscription)
        subscription.mid = self.client.subscribe(subscription.topic)
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

    def on_connect(self, client, userdata, flags, rc):  # pylint: disable=unused-argument,invalid-name
        """Callback function for MQTT Connect

        Parameters
        ----------
        client : _type_
            _description_
        userdata : _type_
            _description_
        flags : _type_
            _description_
        rc : _type_
            _description_
        """
        self.logger.info("Connected with result code %s", rc)
        if rc == 0:
            self.connected = True
            for subscription in self.client_args.subscriptions:
                self.logger.info("MQTT Client %s Subscribing to %s", self.client_args.odoo_id, subscription)
                self.add_subscription(subscription)
        else:
            self.logger.warning("MQTT Connection failed with result code %s", rc)

    def on_disconnect(self, client, userdata, rc):  # pylint: disable=unused-argument,invalid-name
        """Callback function for MQTT Disconnect"""
        self.logger.info("MQTT Client Disconnected with result code %s", rc)
        self.connected = False

    def on_message(self, client, userdata, msg):  # pylint: disable=unused-argument
        """Callback function for MQTT Message

        Parameters
        ----------
        client : _type_
            _description_
        userdata : _type_
            _description_
        msg : _type_
            _description_
        """
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
        """Callback function for MQTT Subscribe

        Parameters
        ----------
        client : _type_
            _description_
        userdata : _type_
            _description_
        mid : _type_
            _description_
        granted_qos : _type_
            _description_
        """
        self.logger.info("Subscribed: %s %s", mid, granted_qos)

    def on_connect_fail(self, client, userdata, rc):  # pylint: disable=unused-argument,invalid-name
        """Callback function for MQTT Connect Fail

        Parameters
        ----------
        client : _type_
            _description_
        userdata : _type_
            _description_
        rc : _type_
            _description_
        """
        self.logger.warning("Connection failed with result code %s", rc)

    def on_unsubscribe(self, client, userdata, mid):  # pylint: disable=unused-argument,invalid-name
        """Callback function for MQTT Unsubscribe

        Parameters
        ----------
        client : _type_
            _description_
        userdata : _type_
            _description_
        mid : _type_
            _description_
        """
        self.logger.info("Unsubscribed from Topic: %s", mid)

    def run(self):
        """Gets called when thread starts"""
        if self.client_args.mqtt_username and self.client_args.mqtt_password:
            self.logger.debug("Setting MQTT Credentials")
            self.client.username_pw_set(self.client_args.mqtt_username, self.client_args.mqtt_password)
        self.logger.info("Connecting to MQTT Broker: %s", self.client_args.mqtt_host)
        self.client.connect(self.client_args.mqtt_host, self.client_args.mqtt_port)
        self.running = True
        while self.running:
            self.client.loop()

    def start(self):
        """Starts the thread. Delays until thread is running or timeout is reached to avoid race conditions"""
        self.logger.info("Starting MQTT Thread: %s", self.client_args.odoo_id)
        super().start()
        # Hold until Thread is reported running
        timeout = 2
        curr_time = time.time()
        while not self.running and time.time() < curr_time + timeout:
            time.sleep(0.1)

        # Check if the Callback Works
        if not odoo_check_connection(self.client_args.odoo_base_url, self.client_args.odoo_mqtt_token):
            self.logger.exception("Odoo Connection Check failed. Stopping MQTT Thread %s", self.client_args.odoo_id)
            self.stop()

    def stop(self):
        """Gets called when thread stops"""
        self.logger.info("Stopping MQTT Thread %s", self.client_args.odoo_id)
        self.running = False
        self.client.disconnect()
