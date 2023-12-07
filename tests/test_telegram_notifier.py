import unittest
from unittest.mock import patch


from ringr.notifiers.telegram_notifier import TelegramNotifier, TelegramNotifierConfig


class TelegramNotifierTestCase(unittest.TestCase):
    config = TelegramNotifierConfig(
        type='telegram',
        api_token=':my_api_token:',
        chat_id='my_chat_id',
        message='the message'
    )

    def setUp(self):
        urllib_patcher = patch('ringr.notifiers.telegram_notifier.urllib.request')
        self.mock_request = urllib_patcher.start()
        self.addCleanup(urllib_patcher.stop)

        self.notifier = TelegramNotifier(self.config)

    def test_notify_detected(self):
        self.notifier.notify(True)

        expected_url = 'https://api.telegram.org/bot:my_api_token:/sendMessage'
        expected_payload = '{"chat_id": "my_chat_id", "text": "the message"}'.encode()
        expected_headers = {'Content-Type': 'application/json'}
        self.mock_request.Request.assert_called_once_with(expected_url, expected_payload,
                                                          headers=expected_headers)

        self.mock_request.urlopen.assert_called_once()

    def test_notify_undetected(self):
        self.notifier.notify(False)

        self.mock_request.urlopen.assert_not_called()
