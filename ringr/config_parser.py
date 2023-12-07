import os
from configparser import ConfigParser

from typing import Any


class EnvConfigParser(ConfigParser):
    ENV_PREFIX = 'RINGR'

    def get(self, section: str, option: str, *args, **kwargs) -> Any:
        env_var = f'{self.ENV_PREFIX}_{section.upper()}_{option.upper()}'
        return os.environ.get(env_var) or super().get(section, option, *args, **kwargs)
