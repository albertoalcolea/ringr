import os
from pathlib import Path
import logging

from dataclasses import dataclass
from typing import Optional

from .config_parser import EnvConfigParser
from .notifiers import parse_notifier_config, NotifierConfig


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectorConfig:
    device: int
    cooldown_secs: float
    threshold: float
    peak_duration: float
    frequency: int
    block_duration: int
    acceptance_ratio: float = 100
    num_freq_bins: int = 256
    gain: int = 0
    latency: Optional[float] = None
    log_analysis: bool = False

    @classmethod
    def configure(cls, conf: EnvConfigParser):
        return cls(
            device=conf.getint('detector', 'device'),
            cooldown_secs=conf.getfloat('detector', 'cooldown'),
            threshold=conf.getfloat('detector', 'threshold'),
            peak_duration=conf.getfloat('detector', 'peak_duration'),
            frequency=conf.getint('detector', 'frequency'),
            block_duration=conf.getint('detector', 'block_duration'),
            acceptance_ratio=conf.getfloat('detector', 'acceptance_ratio', fallback=cls.acceptance_ratio),
            num_freq_bins=conf.getint('detector', 'frequency_bins', fallback=cls.num_freq_bins),
            gain=conf.getint('detector', 'gain', fallback=cls.gain),
            latency=conf.getfloat('detector', 'latency', fallback=cls.latency),
            log_analysis=conf.getboolean('detector', 'log_analysis', fallback=cls.log_analysis),
        )


@dataclass(frozen=True)
class Config:
    detector: DetectorConfig
    notifier: NotifierConfig


def load_config(file: Path) -> Config:
    parser = EnvConfigParser()
    if os.path.isfile(file):
        parser.read(file)

    notifier_config = parse_notifier_config(parser)
    detector_config = DetectorConfig.configure(parser)
    config = Config(detector_config, notifier_config)

    log.debug('Config used: %s', config)
    return config
