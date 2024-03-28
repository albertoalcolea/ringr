import json
import logging
import threading

from dataclasses import dataclass
from typing import Optional

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
    def __init__(self, config: HANotifierConfig) -> None:
        self.config = config
        self._connected_event = threading.Event()

        self.mqtt = paho.Client(client_id=self.config.mqtt_client_id)
        if self.config.mqtt_user and self.config.mqtt_pass:
            self.mqtt.username_pw_set(username=self.config.mqtt_user, password=self.config.mqtt_pass)
        self.mqtt.on_connect = self._on_mqtt_connect
        self.mqtt.on_disconnect = self._on_mqtt_disconnect
        self.mqtt.on_publish = self._on_mqtt_publish
        self.mqtt.connect(host=self.config.mqtt_host, port=self.config.mqtt_port)
        self.mqtt.loop_start()

        # Synchronous wait until client is connected
        self._connected_event.wait()

        self._send_config()

    def notify(self, state: bool) -> None:
        topic = f'homeassistant/binary_sensor/{self.config.device_id}/state'
        payload = {'state': 'ON' if state else 'OFF'}
        msg_info = self.mqtt.publish(topic, json.dumps(payload), retain=True, qos=self.config.mqtt_qos)
        log.info('Notified state changed [%s]: %s', msg_info.mid, payload)

    def _send_config(self) -> None:
        topic = f'homeassistant/binary_sensor/{self.config.device_id}/config'
        payload = {
            'name': self.config.device_id,
            'unique_id': self.config.device_id,
            'device': {
                'name': self.config.device_name,
                'identifiers': [self.config.device_id]
            },
            'manufacturer': __author__,
            'model': __title__,
            'sw_version': __version__,
            'device_class': 'sound',
            'state_topic': f'homeassistant/binary_sensor/{self.config.device_id}/state',
            'value_template': '{{ value_json.state }}',
        }
        msg_info = self.mqtt.publish(topic, json.dumps(payload), retain=True, qos=self.config.mqtt_qos)
        log.info('Notified device config.py [%s]: %s', msg_info.mid, payload)

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == paho.CONNACK_ACCEPTED:
            log.debug('MQTT client connected. Flags: %s', flags)
            self._connected_event.set()
        else:
            log.error('MQTT connection error. Code: %s', rc)

    def _on_mqtt_disconnect(self, client, userdata, rc):
        log.debug('MQTT client disconnected: %s', rc)

    def _on_mqtt_publish(self, client, userdata, mid):
        log.debug('MQTT PUBACK received for message %s', mid)
