from abc import ABC, abstractmethod

from dataclasses import dataclass
from typing import Type

from ringr.config_parser import EnvConfigParser


@dataclass(frozen=True)
class NotifierConfig(ABC):
    type: str

    @classmethod
    def configure(cls: Type['NotifierConfig'], conf: EnvConfigParser):
        raise NotImplementedError()


class Notifier(ABC):
    @abstractmethod
    def notify(self, state: bool) -> None:
        raise NotImplementedError()
