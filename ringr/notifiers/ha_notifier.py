import json
import logging
import threading

from dataclasses import dataclass
from typing import Union, Optional

import paho.mqtt.client as paho

from ringr import __title__, __version__, __author__
from ringr.notifiers.notifier import Notifier, NotifierConfig
from ringr.config_parser import EnvConfigParser


log = logging.getLogger('ringr')


@dataclass(frozen=True)
class HANotifierConfig(NotifierConfig):
    mqtt_host: str
    mqtt_port: int = 1883
    mqtt_user: Optional[str] = None
    mqtt_pass: Optional[str] = None
    mqtt_client_id: str = 'ringr_01'
    mqtt_qos: int = 1
    device_id: str = 'ringr_01'
    device_name: str = 'ringr 01'

    @classmethod
    def configure(cls, conf: EnvConfigParser):
        return cls(
            type=conf.get('notifier', 'type'),
            device_id=conf.get('notifier', 'device_id', fallback=cls.device_id),
            device_name=conf.get('notifier', 'device_name', fallback=cls.device_name),
            mqtt_host=conf.get('notifier', 'mqtt_host'),
            mqtt_port=conf.getint('notifier', 'mqtt_port', fallback=cls.mqtt_port),
            mqtt_user=conf.get('notifier', 'mqtt_user', fallback=cls.mqtt_user),
            mqtt_pass=conf.get('notifier', 'mqtt_pass', fallback=cls.mqtt_pass),
            mqtt_client_id=conf.get('notifier', 'mqtt_client_id', fallback=cls.mqtt_client_id),
            mqtt_qos=conf.getint('notifier', 'mqtt_qos', fallback=cls.mqtt_qos),
        )


class HANotifier(Notifier):
    ha_status_topic = 'homeassistant/status'
    ha_status_online_payload = b'online'
    dev_online_payload = b'online'
    dev_offline_payload = b'offline'
    dev_detected_payload = b'ON'
    dev_undetected_payload = b'OFF'

    def __init__(self, config: HANotifierConfig) -> None:
        self.config = config
        self.state = False
        self._connected_event = threading.Event()

        self.state_topic = f'homeassistant/binary_sensor/{self.config.device_id}/state'
        self.availability_topic = f'homeassistant/binary_sensor/{self.config.device_id}/availability'

        self.mqtt = paho.Client(client_id=self.config.mqtt_client_id)
        if self.config.mqtt_user and self.config.mqtt_pass:
            self.mqtt.username_pw_set(username=self.config.mqtt_user, password=self.config.mqtt_pass)
        self.mqtt.on_connect = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_publish = self._on_mqtt_publish
        self.mqtt.on_subscribe = self._on_mqtt_subscribe
        self.mqtt.on_message = self._on_mqtt_message
        self.mqtt.will_set(self.availability_topic, self.dev_offline_payload, qos=self.config.mqtt_qos, retain=True)
        self.mqtt.connect(host=self.config.mqtt_host, port=self.config.mqtt_port)
        self.mqtt.loop_start()

        # Synchronous wait until client is connected
        self._connected_event.wait()

        self._subscribe(self.ha_status_topic)
        self._send_config()

    def notify(self, state: bool) -> None:
        self.state = state
        self._send_state()

    def _send_config(self) -> None:
        topic = f'homeassistant/binary_sensor/{self.config.device_id}/config'
        payload = {
            'name': self.config.device_id,
            'unique_id': self.config.device_id,
            'device': {
                'identifiers': [self.config.device_id],
                'name': self.config.device_name,
                'manufacturer': __author__,
                'model': __title__,
                'sw_version': __version__,
            },
            'device_class': 'sound',
            'state_topic': self.state_topic,
            'availability_topic': self.availability_topic,
        }
        if self._publish(topic, json.dumps(payload)):
            log.info('Notified discovery device config: %s', payload)

    def _send_state(self) -> None:
        payload = self.dev_detected_payload if self.state else self.dev_undetected_payload
        if self._publish(self.state_topic, payload):
            log.info('Notified state changed: %s', payload.decode('UTF-8'))

    def _send_availability(self) -> None:
        if self._publish(self.availability_topic, self.dev_online_payload):
            log.info('Notified device available')

    def _publish(self, topic: str, payload: Union[str, bytes]) -> bool:
        msg_info = self.mqtt.publish(topic, payload=payload, qos=self.config.mqtt_qos, retain=True)
        if msg_info.rc == paho.MQTT_ERR_SUCCESS:
            log.debug('MQTT PUBLISH sent to topic %s. Message ID: %s', topic, msg_info.mid)
            return True
        else:
            log.error('Unable to publish MQTT message to topic %s. Client is not connected', topic)
            return False

    def _subscribe(self, topic: str) -> bool:
        rc, mid = self.mqtt.subscribe(topic)
        if rc == paho.MQTT_ERR_SUCCESS:
            log.debug('MQTT SUBSCRIBE sent to topic %s. Message ID: %s', topic, mid)
            return True
        else:
            log.error('Unable to subscribe to MQTT topic %s. Client is not connected', topic)
            return False

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == paho.CONNACK_ACCEPTED:
            log.debug('MQTT client connected. Flags: %s', flags)
            self._connected_event.set()
            self._send_availability()
        else:
            log.error('MQTT connection error. Code: %s', rc)

    def _on_mqtt_disconnect(self, client, userdata, rc):
        log.debug('MQTT client disconnected: %s', rc)

    def _on_mqtt_publish(self, client, userdata, mid):
        log.debug('MQTT PUBACK received for message %s', mid)

    def _on_mqtt_subscribe(self, client, userdata, mid, granted_qos):
        log.debug('MQTT SUBACK received for message %s', mid)

    def _on_mqtt_message(self, client, userdata, msg):
        if msg.topic == self.ha_status_topic and msg.payload == self.ha_status_online_payload:
            log.info('Home Assistant MQTT integration start detected. Resending discovery message')
            self._send_config()
