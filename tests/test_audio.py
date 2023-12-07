import unittest
from unittest.mock import Mock, MagicMock, patch

import numpy as np

from ringr.audio import AudioDetector
from ringr.config import DetectorConfig


class AudioDetectorTestCase(unittest.TestCase):
    config = DetectorConfig(
        device=1,
        cooldown_secs=10,
        threshold=65,
        peak_duration=1.5,
        frequency=1000,
        block_duration=50,
        acceptance_ratio=95,
        num_freq_bins=256,
        gain=200,
        latency=0.1,
        log_analysis=False
    )

    def setUp(self):
        self.notifier = Mock()

        AudioDetector.get_samplerate = Mock(return_value=44100)

        self.sliding_window = MagicMock()

        self.detector = AudioDetector(self.config, self.notifier)
        self.detector.sliding_window = self.sliding_window

        self.data = np.full([2205, 2], 1000)  # blocksize

    def test_initial_parameters(self):
        self.assertEqual(1, self.detector.device)
        self.assertEqual(44100, self.detector.samplerate)
        self.assertEqual(0.1, self.detector.latency)
        self.assertEqual(50, self.detector.block_duration)
        self.assertEqual(2205, self.detector.blocksize)  # 50 ms at 44100 samples per second
        self.assertEqual(0.65, self.detector.threshold)
        self.assertEqual(1.5, self.detector.peak_duration)
        self.assertEqual(30, self.detector.peak_blocks)  # TODO: review
        self.assertEqual(95, self.detector.acceptance_ratio)
        self.assertEqual(28.5, self.detector.acceptable_peak_blocks)
        self.assertEqual(256, self.detector.num_freq_bins)
        self.assertEqual(200, self.detector.gain)

        # FFT
        self.assertEqual(510, self.detector.fftsize)
        self.assertEqual(12, self.detector.freq_bin_idx)

    def test_fft_filter(self):
        # This does not test the actual FFT calculation, this is delegated to numpy, but it tests there is
        # no undesired side effect or exception thrown
        self.assertAlmostEqual(9.634e-13, self.detector.get_fft_magnitude(self.data), delta=0.001)

    def test_process_value_not_enough_samples(self):
        # Fast exit if there is not enough samples in the sliding window
        self.sliding_window.__len__.return_value = 1

        self.assertFalse(self.detector.process_value(1))
        self.sliding_window.add.assert_called_once_with(True)
        self.sliding_window.window.count.assert_not_called()

    def test_process_value_match(self):
        self.sliding_window.__len__.return_value = 31   # higher than peak blocks. TODO: review
        self.sliding_window.window.count.return_value = 29

        self.assertTrue(self.detector.process_value(1))

    def test_process_value_under_acceptance_ratio(self):
        self.sliding_window.__len__.return_value = 31   # higher than peak blocks. TODO: review
        self.sliding_window.window.count.return_value = 28

        self.assertFalse(self.detector.process_value(1))

    def test_process_value_added_sample_under_threshold(self):
        self.detector.process_value(0.64)
        self.sliding_window.add.assert_called_once_with(False)

    def test_process_value_added_sample_equal_to_threshold(self):
        self.detector.process_value(0.65)
        self.sliding_window.add.assert_called_once_with(False)

    def test_process_value_added_sample_above_threshold(self):
        self.detector.process_value(0.66)
        self.sliding_window.add.assert_called_once_with(True)

    @patch('ringr.audio.time')
    def test_analyze_not_detected(self, mock_time):
        self.detector.last_detection_time = 0
        self.detector.last_state = False
        mock_time.time.return_value = 15
        self.notifier.notify.reset_mock()

        self.detector.get_fft_magnitude = Mock()
        self.detector.process_value = Mock(return_value=False)

        self.detector.analyze(self.data)

        self.assertFalse(self.detector.last_state)
        self.notifier.notify.assert_not_called()

    @patch('ringr.audio.time')
    def test_analyze_detected(self, mock_time):
        self.detector.last_detection_time = 0
        self.detector.last_state = False
        mock_time.time.return_value = 15
        self.notifier.notify.reset_mock()

        self.detector.get_fft_magnitude = Mock()
        self.detector.process_value = Mock(return_value=True)

        self.detector.analyze(self.data)

        self.assertTrue(self.detector.last_state)
        self.assertEqual(15, self.detector.last_detection_time)
        self.notifier.notify.assert_called_once_with(True)

    @patch('ringr.audio.time')
    def test_analyze_cooldown_time(self, mock_time):
        self.detector.last_detection_time = 0
        self.detector.last_state = True
        mock_time.time.return_value = 9
        self.notifier.notify.reset_mock()

        self.detector.get_fft_magnitude = Mock()
        self.detector.process_value = Mock()

        self.detector.analyze(self.data)

        self.assertTrue(self.detector.last_state)
        self.notifier.notify.assert_not_called()

    @patch('ringr.audio.time')
    def test_analyze_reset_cooldown_time(self, mock_time):
        self.detector.last_detection_time = 0
        self.detector.last_state = True
        mock_time.time.return_value = 16
        self.notifier.notify.reset_mock()

        self.detector.get_fft_magnitude = Mock()
        self.detector.process_value = Mock(return_value=False)

        self.detector.analyze(self.data)

        self.assertFalse(self.detector.last_state)
        self.notifier.notify.assert_called_once_with(False)
