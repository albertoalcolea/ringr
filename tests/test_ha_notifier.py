import unittest
from unittest.mock import Mock, patch, call

import logging

import paho.mqtt.client as paho
from paho.mqtt.client import MQTTMessage

from ringr import __version__
from ringr.notifiers.ha_notifier import HANotifier, HANotifierConfig


# Don't show logging messages while testing
logging.disable(logging.CRITICAL)


class HANotifierTestCase(unittest.TestCase):
    config = HANotifierConfig(
        type='ha',
        device_id='ringr_01',
        device_name='ringr 01',
        mqtt_host='localhost',
        mqtt_port=1883,
        mqtt_user='ringr_user',
        mqtt_pass='ringr_pass',
        mqtt_client_id='ringr_mqtt_01',
        mqtt_qos=1
    )

    config_payload = ('{"name": "ringr_01", '
                      '"unique_id": "ringr_01", '
                      '"device": {'
                      '"identifiers": ["ringr_01"], '
                      '"name": "ringr 01", '
                      '"manufacturer": "Alberto Alcolea", '
                      '"model": "ringr", '
                      f'"sw_version": "{__version__}"'
                      '}, '
                      '"device_class": "sound", '
                      '"state_topic": "homeassistant/binary_sensor/ringr_01/state", '
                      '"availability_topic": "homeassistant/binary_sensor/ringr_01/availability"}')

    def setUp(self):
        paho_patcher = patch('ringr.notifiers.ha_notifier.paho')
        self.mock_paho = paho_patcher.start()
        self.addCleanup(paho_patcher.stop)

        threading_patcher = patch('ringr.notifiers.ha_notifier.threading')
        self.mock_threading = threading_patcher.start()
        self.addCleanup(threading_patcher.stop)

        self.connected_event = Mock()
        self.mock_threading.Event = Mock(return_value=self.connected_event)

        self.mqtt = Mock()
        self.mqtt.subscribe = Mock(return_value=(paho.MQTT_ERR_SUCCESS, 0))

        self.mock_paho.Client = Mock(return_value=self.mqtt)
        self.mock_paho.CONNACK_ACCEPTED = 0

        self.notifier = HANotifier(self.config)

    def test_connect(self):
        self.mock_paho.Client.assert_called_once_with(client_id='ringr_mqtt_01')
        self.mqtt.username_pw_set.asset_called_once_with(username='ringr_user', password='ringr_pass')
        self.mqtt.connect.assert_called_once_with(host='localhost', port=1883)
        self.mqtt.loop_start.assert_called_once()
        self.connected_event.wait.assert_called_once()

    def test_connect_no_auth(self):
        config = HANotifierConfig(
            type='ha',
            device_id='ringr_01',
            device_name='ringr 01',
            mqtt_host='localhost',
            mqtt_port=1883,
            mqtt_client_id='ringr_mqtt_01',
            mqtt_qos=1
        )

        self.mqtt = Mock()
        self.mqtt.subscribe = Mock(return_value=(paho.MQTT_ERR_SUCCESS, 0))
        self.mock_paho.Client = Mock(return_value=self.mqtt)

        self.notifier = HANotifier(config)

        self.mqtt.username_pw_set.assert_not_called()

    def test_on_connect_accepted(self):
        self.notifier._on_mqtt_connect(None, None, None, 0)

        self.connected_event.set.assert_called_once()

    def test_on_connect_error(self):
        self.notifier._on_mqtt_connect(None, None, None, 1)

        self.connected_event.set.assert_not_called()

    def test_publish_availability_on_connect(self):
        self.notifier._on_mqtt_connect(None, None, None, 0)

        expected_topic = 'homeassistant/binary_sensor/ringr_01/availability'
        expected_payload = b'online'

        self.mqtt.publish.assert_called_with(expected_topic, payload=expected_payload, qos=1, retain=True)

    def test_publish_discovery_config_message_on_connect(self):
        expected_topic = 'homeassistant/binary_sensor/ringr_01/config'
        expected_payload = self.config_payload

        self.mqtt.publish.assert_called_once_with(expected_topic, payload=expected_payload, qos=1, retain=True)

    def test_subscribed_to_ha_status_topic_on_connect(self):
        self.mqtt.subscribe.assert_called_once_with('homeassistant/status')

    def test_set_last_will_message(self):
        expected_topic = 'homeassistant/binary_sensor/ringr_01/availability'
        expected_payload = b'offline'

        self.mqtt.will_set.assert_called_once_with(expected_topic, expected_payload, qos=1, retain=True)

    def test_notify_detected(self):
        self.notifier.notify(True)

        expected_topic = 'homeassistant/binary_sensor/ringr_01/state'
        expected_payload = b'ON'

        self.mqtt.publish.assert_called_with(expected_topic, payload=expected_payload, qos=1, retain=True)

    def test_notify_undetected(self):
        self.notifier.notify(False)

        expected_topic = 'homeassistant/binary_sensor/ringr_01/state'
        expected_payload = b'OFF'

        self.mqtt.publish.assert_called_with(expected_topic, payload=expected_payload, qos=1, retain=True)

    def test_resend_discovery_config_message_on_ha_birth_message(self):
        msg = MQTTMessage()
        msg.topic = b'homeassistant/status'
        msg.payload = b'online'

        self.notifier._on_mqtt_message(None, None, msg)

        expected_topic = 'homeassistant/binary_sensor/ringr_01/config'
        expected_payload = self.config_payload

        # First call sent on init
        # Second call sent after receiving birth message from HA
        self.mqtt.publish.assert_has_calls([
            call(expected_topic, payload=expected_payload, qos=1, retain=True),
            call(expected_topic, payload=expected_payload, qos=1, retain=True),
        ])
