import unittest
from unittest.mock import patch

from ringr.config_parser import EnvConfigParser


class ConfigParserTestCase(unittest.TestCase):

    @patch.dict('os.environ', {}, clear=True)
    def test_from_file(self):
        parser = EnvConfigParser()
        parser.read_dict({
            'section1': {
                'value1': '123'
            }
        })

        self.assertEqual('123', parser.get('section1', 'value1'))
        self.assertEqual(123, parser.getint('section1', 'value1'))

    @patch.dict('os.environ', {
        'RINGR_SECTION1_VALUE1': '999'
    }, clear=True)
    def test_env_var_takes_preference(self):
        parser = EnvConfigParser()
        parser.read_dict({
            'section1': {
                'value1': '123'
            }
        })

        self.assertEqual('999', parser.get('section1', 'value1'))
        self.assertEqual(999, parser.getint('section1', 'value1'))

    @patch.dict('os.environ', {}, clear=True)
    def test_fallback(self):
        parser = EnvConfigParser()
        parser.read_dict({
            'section1': {
                'value1': '123'
            }
        })

        self.assertEqual('333', parser.get('section1', 'unknown', fallback='333'))
