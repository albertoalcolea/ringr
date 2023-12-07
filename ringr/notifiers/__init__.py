from typing import cast

from ringr.notifiers.notifier import Notifier, NotifierConfig
from ringr.notifiers.ha_notifier import HANotifier, HANotifierConfig
from ringr.notifiers.telegram_notifier import TelegramNotifier, TelegramNotifierConfig
from ringr.config_parser import EnvConfigParser
from ringr.exceptions import RingDetectorError


__all__ = [
    'create_notifier',
    'parse_notifier_config',
    'Notifier', 'NotifierConfig',
    'HANotifier', 'HANotifierConfig',
    'TelegramNotifier', 'TelegramNotifierConfig'
]


def parse_notifier_config(config: EnvConfigParser):
    notifier_type = config['notifier']['type']
    if notifier_type == 'ha':
        return HANotifierConfig.configure(config)
    elif notifier_type == 'telegram':
        return TelegramNotifierConfig.configure(config)
    else:
        raise RingDetectorError(f'Unsupported notifier: {config.type}')


def create_notifier(config: NotifierConfig) -> Notifier:
    if config.type == 'ha':
        return HANotifier(cast(HANotifierConfig, config))
    elif config.type == 'telegram':
        return TelegramNotifier(cast(TelegramNotifierConfig, config))
    else:
        raise RingDetectorError(f'Unsupported notifier: {config.type}')
