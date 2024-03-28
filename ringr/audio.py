import math
import time
import logging

from typing import Any

import sounddevice as sd
import numpy as np

from .config import DetectorConfig
from .notifiers import Notifier


log = logging.getLogger('ringr')


class SlidingWindow:
    def __init__(self, size):
        self.size = size
        self.window = []

    def add(self, value):
        if len(self.window) == self.size:
            self.window.pop(0)
        self.window.append(value)

    def __len__(self):
        return len(self.window)

    def __repr__(self):
        return str(self.window)


class AudioDetector:
    def __init__(self, config: DetectorConfig, notifier: Notifier) -> None:
        self.config = config
        self.notifier = notifier

        self.device = self.config.device
        self.threshold = self.config.threshold / 100.0
        self.peak_duration = self.config.peak_duration
        self.acceptance_ratio = self.config.acceptance_ratio
        self.frequency = self.config.frequency
        self.num_freq_bins = self.config.num_freq_bins
        self.block_duration = self.config.block_duration
        self.gain = self.config.gain
        self.latency = 'high' if self.config.latency is None else self.config.latency

        self.samplerate = self.get_samplerate(self.device)
        self.blocksize = int(self.samplerate * self.block_duration / 1000)
        self.peak_blocks = int(self.samplerate * self.peak_duration / self.blocksize)
        self.acceptable_peak_blocks = self.peak_blocks * self.acceptance_ratio / 100.0
        self.sliding_window = SlidingWindow(self.peak_blocks)
        self.last_detection_time = 0

        # Notes:
        #   samplerate / 2: maximum frequency that can be correctly captured
        #   num_freq_bins: number of bins for the fft
        #   fftsize: size of the fft bin
        #   freq_bin_idx: bin index for the desired frequency to analyze
        max_freq = self.samplerate / 2
        delta_f = max_freq / (self.num_freq_bins - 1)
        self.fftsize = math.ceil(self.samplerate / delta_f)
        self.freq_bin_idx = math.ceil(self.frequency / delta_f)

        self.last_state = None
        self.update_state(False)

    @staticmethod
    def get_samplerate(device: int) -> int:
        """ Get default samplerate of the input sound device """
        return sd.query_devices(device, 'input')['default_samplerate']

    def start(self) -> None:
        with sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            latency=self.latency,
            callback=self.callback
        ):
            while True:
                time.sleep(1)

    def callback(self, indata: np.ndarray, frames: int, stime: Any, status: sd.CallbackFlags) -> None:
        """This is called (from a separate thread) for each audio block."""
        if status:
            log.error('Error status: %s', status)
        if any(indata):
            self.analyze(indata)
        else:
            log.debug('No input')

    def analyze(self, data: np.ndarray) -> None:
        magnitude = self.get_fft_magnitude(data)
        detected = self.process_value(magnitude)
        # Cooldown reset check
        if self.last_state:
            if (time.time() - self.last_detection_time) < self.config.cooldown_secs:
                # Do nothing during cooldown time
                return
            else:
                self.update_state(False)
        # Detection
        if detected:
            log.info('Sound event detected')
            self.last_detection_time = time.time()
            self.update_state(True)

    def get_fft_magnitude(self, data: np.ndarray) -> float:
        magnitudes = np.abs(np.fft.rfft(data[:, 0], n=self.fftsize))
        magnitude = magnitudes[self.freq_bin_idx]
        magnitude *= self.gain / self.fftsize
        magnitude = np.clip(magnitude, 0, 1)  # normalized between 0 and 1, limit values
        return magnitude

    def process_value(self, value: float) -> bool:
        matches = value > self.threshold
        self.sliding_window.add(matches)
        if len(self.sliding_window) < self.peak_blocks:
            # We need more samples to take a decision
            return False
        num_matches = self.sliding_window.window.count(True)
        if self.config.log_analysis:
            log.debug('Value %s - Threshold %s - num_matches %s - acceptable %s', value, self.threshold,
                      num_matches, self.acceptable_peak_blocks)
        return num_matches >= self.acceptable_peak_blocks

    def update_state(self, new_state: bool):
        self.last_state = new_state
        self.notifier.notify(new_state)
