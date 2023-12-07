import unittest
from unittest.mock import patch

from ringr.config_parser import EnvConfigParser
from ringr.config import DetectorConfig


class ConfigTestCase(unittest.TestCase):

    @patch.dict('os.environ', {}, clear=True)
    def test_detector_config(self):
        parser = EnvConfigParser()
        parser.read_dict({
            'detector': {
                'device': '1',
                'cooldown': '10',
                'threshold': '60',
                'peak_duration': '0.8',
                'acceptance_ratio': '0.85',
                'frequency': '1000',
                'frequency_bins': '256',
                'gain': '200',
                'block_duration': '50',
                'latency': '0.1',
                'log_analysis': 'True',
            }
        })

        detector_config = DetectorConfig.configure(parser)
        expected = DetectorConfig(
            device=1,
            cooldown_secs=10,
            threshold=60,
            peak_duration=0.8,
            acceptance_ratio=0.85,
            frequency=1000,
            num_freq_bins=256,
            gain=200,
            block_duration=50,
            latency=0.1,
            log_analysis=True
        )
        self.assertEqual(expected, detector_config)

    @patch.dict('os.environ', {
        'RINGR_DETECTOR_DEVICE': '1',
        'RINGR_DETECTOR_COOLDOWN': '10',
        'RINGR_DETECTOR_THRESHOLD': '60',
        'RINGR_DETECTOR_PEAK_DURATION': '0.8',
        'RINGR_DETECTOR_ACCEPTANCE_RATIO': '0.85',
        'RINGR_DETECTOR_FREQUENCY': '1000',
        'RINGR_DETECTOR_FREQUENCY_BINS': '256',
        'RINGR_DETECTOR_GAIN': '200',
        'RINGR_DETECTOR_BLOCK_DURATION': '50',
        'RINGR_DETECTOR_LATENCY': '0.1',
        'RINGR_DETECTOR_LOG_ANALYSIS': 'True',
    }, clear=True)
    def test_detector_config_from_env(self):
        parser = EnvConfigParser()
        parser['detector'] = {}
        parser['detector']['device'] = '2'

        detector_config = DetectorConfig.configure(parser)
        expected = DetectorConfig(
            device=1,
            cooldown_secs=10,
            threshold=60,
            peak_duration=0.8,
            acceptance_ratio=0.85,
            frequency=1000,
            num_freq_bins=256,
            gain=200,
            block_duration=50,
            latency=0.1,
            log_analysis=True
        )
        self.assertEqual(expected, detector_config)

    @patch.dict('os.environ', {}, clear=True)
    def test_optional_params(self):
        parser = EnvConfigParser()
        parser.read_dict({
            'detector': {
                'device': '1',
                'cooldown': '10',
                'threshold': '60',
                'peak_duration': '0.8',
                'acceptance_ratio': '0.85',
                'frequency': '1000',
                'frequency_bins': '256',
                'gain': '200',
                'block_duration': '50',
            }
        })

        detector_config = DetectorConfig.configure(parser)
        expected = DetectorConfig(
            device=1,
            cooldown_secs=10,
            threshold=60,
            peak_duration=0.8,
            acceptance_ratio=0.85,
            frequency=1000,
            num_freq_bins=256,
            gain=200,
            block_duration=50,
            latency=None,
            log_analysis=False
        )
        self.assertEqual(expected, detector_config)
