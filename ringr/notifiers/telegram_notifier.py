import urllib.request
import json
import logging

from dataclasses import dataclass

from ringr.notifiers.notifier import Notifier, NotifierConfig
from ringr.config_parser import EnvConfigParser

log = logging.getLogger('ringr')


@dataclass(frozen=True)
class TelegramNotifierConfig(NotifierConfig):
    api_token: str
    chat_id: str
    message: str = 'Event detected'

    @classmethod
    def configure(cls, conf: EnvConfigParser):
        return cls(
            type=conf.get('notifier', 'type'),
            api_token=conf.get('notifier', 'api_token'),
            chat_id=conf.get('notifier', 'chat_id'),
            message=conf.get('notifier', 'message', fallback=cls.message),
        )


class TelegramNotifier(Notifier):
    url_formatter = 'https://api.telegram.org/bot{api_token}/sendMessage'

    def __init__(self, config: TelegramNotifierConfig):
        self.config = config
        url = self.url_formatter.format(api_token=self.config.api_token)
        payload = {
            'chat_id': self.config.chat_id,
            'text': self.config.message
        }
        self.request = urllib.request.Request(url, json.dumps(payload).encode(),
                                              headers={'Content-Type': 'application/json'})

    def notify(self, state: bool) -> None:
        if state:
            response = urllib.request.urlopen(self.request)
            if response.status != 200:
                log.error('Error notifying detection to telegram bot. Status code: %d', response.status)
            log.debug('Notified detection')
